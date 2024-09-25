import json
import logging

import httpx
from app.api.chat import chat_proxy
from app.core.security import verify_token
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.rag import AddToDBRequest, RAGRequest
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.post("/rag/", dependencies=[Depends(verify_token)])
async def rag(rag_request: RAGRequest) -> ChatResponse:
    # retrieve a prompt with context
    async with httpx.AsyncClient() as client:
        try:
            rag_response = await client.post(
                "http://rag_service:8000/prompt_w_context/",
                json=rag_request.model_dump(),
                timeout=httpx.Timeout(60.0),
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=500, detail="Failed to connect to RAG service"
            )

    if rag_response.status_code != 200:
        raise HTTPException(
            status_code=rag_response.status_code, detail=rag_response.json()["detail"]
        )

    rag_response = json.loads(rag_response.content)

    chat_response = await chat_proxy(
        ChatRequest(
            message=rag_response["message"],
            model=rag_request.model,
            chat_id=rag_request.chat_id
        )
    )

    return chat_response


@router.post("/add_to_rag_db/", dependencies=[Depends(verify_token)])
async def add_to_db(add_to_db_request: AddToDBRequest):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://rag_service:8000/add_to_rag_db/",
                json=add_to_db_request.model_dump(),
                timeout=httpx.Timeout(60.0),
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=500, detail="Failed to connect to RAG service"
            )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code, detail=response.json()["detail"]
        )


@router.get("/reindex/", dependencies=[Depends(verify_token)])
async def reindex_proxy():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                "http://rag_service:8000/reindex/",
                timeout=httpx.Timeout(60.0),
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=500, detail="Failed to connect to RAG service"
            )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code, detail=response.json()["detail"]
        )