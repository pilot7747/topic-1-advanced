from fastapi import FastAPI, Request, HTTPException, Depends, Security
from fastapi.security import APIKeyHeader, OAuth2PasswordRequestForm
from pydantic import BaseModel
from redis import asyncio as aioredis
import httpx
import json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from databases import Database
from sqlalchemy import create_engine, MetaData, Table, Column, String
from sqlalchemy.sql import select, insert
from passlib.context import CryptContext


ADMIN_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicm9vdCIsImV4cCI6MTc1OTE5ODkxMSwiaWF0IjoxNzIzMTk4OTExfQ.Es-7-MMT5LPP4kW_L-MZxQ4h1pYC29HjNMzx0cYCkgk"
app = FastAPI()

# API Key header for Swagger UI
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

# Setup Redis for chat history and rate limiting
redis = aioredis.from_url("redis://redis:6379")

# Database setup
DATABASE_URL = "postgresql://user:password@postgresdb/dbname"
database = Database(DATABASE_URL)
metadata = MetaData()

# Define users table
users = Table(
    "users",
    metadata,
    Column("username", String, primary_key=True),
    Column("hashed_password", String),
    Column("api_key", String, unique=True),
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Rate limiting configuration
RATE_LIMIT = 5  # max requests per minute
RATE_LIMIT_KEY_PREFIX = "rate_limit"

# Metrics store
metrics = {
    "200x": 0,
    "400x": 0,
    "500x": 0,
    "total_requests": 0,
    "tokens_in": 0,
    "tokens_out": 0,
}


class ChatRequest(BaseModel):
    message: str
    chat_id: str


@app.on_event("startup")
async def startup():
    engine = create_engine(DATABASE_URL)
    metadata.create_all(engine)
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


async def check_token(api_key: str) -> bool:
    if api_key != ADMIN_TOKEN:
        query = select(users).where(users.c.api_key == api_key)
        user = await database.fetch_one(query)
        return user is not None
    return True


async def verify_token(api_key: str = Security(api_key_header)):
    if not api_key:
        raise HTTPException(status_code=403, detail="Unauthorized")
    if not await check_token(api_key):
        raise HTTPException(status_code=403, detail="Unauthorized")


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Allow access to Swagger UI and OpenAPI schema without authentication
        normalized_path = request.url.path.rstrip("/")
        if normalized_path in ["/docs", "/openapi.json", "/signup"]:
            return await call_next(request)

        token = request.headers.get("Authorization")
        if not await check_token(token):
            metrics["400x"] += 1
            return JSONResponse(status_code=403, content={"detail": "Unauthorized"})
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        user_token = request.headers.get("Authorization")
        if not user_token or user_token == ADMIN_TOKEN:
            return await call_next(request)

        user_key = f"{RATE_LIMIT_KEY_PREFIX}:{user_token}"
        count = await redis.get(user_key)
        if count and int(count) >= RATE_LIMIT:
            metrics["400x"] += 1
            return JSONResponse(
                status_code=429, content={"detail": "Rate limit exceeded"}
            )

        await redis.incr(user_key)
        await redis.expire(user_key, 60)
        return await call_next(request)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    metrics["total_requests"] += 1
    response = await call_next(request)
    if 200 <= response.status_code < 300:
        metrics["200x"] += 1
    elif 400 <= response.status_code < 500:
        metrics["400x"] += 1
    elif response.status_code >= 500:
        metrics["500x"] += 1
    return response


@app.post("/signup/")
async def signup(form_data: OAuth2PasswordRequestForm = Depends()):
    query = select(users).where(users.c.username == form_data.username)
    user = await database.fetch_one(query)

    if user:
        raise HTTPException(status_code=400, detail="Username already taken")

    hashed_password = get_password_hash(form_data.password)
    api_key = "token" + str(hash(form_data.username))  # Simple token generation

    query = insert(users).values(
        username=form_data.username,
        hashed_password=hashed_password,
        api_key=api_key,
    )
    await database.execute(query)

    return {"message": "User created successfully", "api_key": api_key}


@app.post("/chat/", dependencies=[Depends(verify_token)])
async def chat_proxy(chat_request: ChatRequest, request: Request):
    # Retrieve chat history from Redis
    chat_history = await redis.lrange(f"chat_history:{chat_request.chat_id}", 0, -1)
    chat_history = [msg.decode() for msg in chat_history]
    chat_history = [json.loads(msg) for msg in chat_history]

    # Proxy the request to the chat service
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://chat_service:8000/chat/",
            json={"message": chat_request.message, "chat_history": chat_history},
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code, detail="Chat service error"
        )

    # Store the new message in Redis
    await redis.rpush(
        f"chat_history:{chat_request.chat_id}",
        json.dumps({"text": chat_request.message, "role": "user"}),
    )
    await redis.rpush(
        f"chat_history:{chat_request.chat_id}",
        json.dumps({"text": response.json()["response"], "role": "assistant"}),
    )

    # Update metrics
    metrics["tokens_in"] += len(chat_request.message.split())
    metrics["tokens_out"] += len(response.json()["response"].split())

    return response.json()


@app.get("/chat/{chat_id}/history", dependencies=[Depends(verify_token)])
async def get_chat_history(chat_id: str):
    # Retrieve chat history from Redis
    chat_history = await redis.lrange(f"chat_history:{chat_id}", 0, -1)

    if not chat_history:
        raise HTTPException(status_code=404, detail="Chat history not found")

    # Decode the history from bytes to strings
    decoded_history = [msg.decode() for msg in chat_history]

    return {"chat_id": chat_id, "history": decoded_history}


@app.get("/metrics/", dependencies=[Depends(verify_token)])
async def get_metrics():
    return metrics


# Apply the middlewares
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthMiddleware)
