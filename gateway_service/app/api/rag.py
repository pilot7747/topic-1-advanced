import httpx
import logging
import json

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import verify_token
from app.core.config import INFERENCE_ROUTING
from app.schemas.rag import RAGRequest, AddToDBRequest

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.post("/rag/", dependencies=[Depends(verify_token)])
async def rag(rag_request: RAGRequest) -> str:
    # retrieve a prompt with context
    async with httpx.AsyncClient() as client:
        try:
            rag_response = await client.post(
                "http://rag_service:8004/prompt_w_context",
                json=rag_request.model_dump(),
                timeout=httpx.Timeout(20.0),
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=500, detail="Failed to connect to RAG service"
            )

    if rag_response.status_code != 200:
        raise HTTPException(
            status_code=rag_response.status_code, detail="RAG service error"
        )

    rag_response = json.loads(rag_response.content)

    # send a prompt into an LLM API
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"http://{INFERENCE_ROUTING[rag_request.model]}:8000/chat/",
                json={"message": rag_response["message"], "chat_history": []},
                timeout=httpx.Timeout(60.0),
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=500, detail="Failed to connect to chat service"
            )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code, detail="Chat service error"
        )

    return response.json()["response"]


@router.post("/add_to_rag_db/", dependencies=[Depends(verify_token)])
async def add_to_db(add_to_db_request: AddToDBRequest):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://rag_service:8004/add_to_rag_db",
                json=add_to_db_request.model_dump(),
                timeout=httpx.Timeout(20.0),
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=500, detail="Failed to connect to RAG service"
            )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code, detail="RAG service error"
        )


@router.get("/reindex/", dependencies=[Depends(verify_token)])
async def reindex_proxy():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "http://rag_service:8004/reindex",
                timeout=httpx.Timeout(20.0),
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=500, detail="Failed to connect to RAG service"
            )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code, detail="RAG service error"
        )