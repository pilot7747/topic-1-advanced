from contextlib import asynccontextmanager

from app.api import auth, chat, metrics, rag
from app.db.database import database
from app.middleware.auth_middleware import AuthMiddleware
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.rate_limit_middleware import RateLimitMiddleware
from app.core.security import verification_app
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    await database.connect()
    yield
    # Shutdown logic
    await database.disconnect()


app1 = FastAPI(lifespan=lifespan)

# Include routers from different modules
app1.include_router(auth.router)
app1.include_router(chat.router)
app1.include_router(metrics.router)
app1.include_router(rag.router)

# Apply middlewares
app1.add_middleware(RateLimitMiddleware)
app1.add_middleware(AuthMiddleware)
app1.add_middleware(LoggingMiddleware)

app = FastAPI()

app.mount("/", app1) # if does not work try: app.mount(app1, "/app1")
app.mount("/verify", verification_app)


import uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)