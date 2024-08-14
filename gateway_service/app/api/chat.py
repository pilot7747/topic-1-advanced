import json

import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.core.metrics import update_tokens_in, update_tokens_out
from app.core.security import verify_token
from app.db.database import redis
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/chat/", dependencies=[Depends(verify_token)])
async def chat_proxy(chat_request: ChatRequest) -> ChatResponse:
    """
    Handles chat proxying requests by interacting with a chat service and storing chat history in Redis.

    :param chat_request: The request payload containing the chat ID and message.
    :type chat_request: ChatRequest
    :return: The response from the chat service encapsulated in a ChatResponse object.
    :rtype: ChatResponse
    """
    chat_history = await redis.lrange(f"chat_history:{chat_request.chat_id}", 0, -1)
    chat_history = [json.loads(msg.decode()) for msg in chat_history]

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://gpt-4-mini:8000/chat/",
            json={"message": chat_request.message, "chat_history": chat_history},
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code, detail="Chat service error"
        )

    await redis.rpush(
        f"chat_history:{chat_request.chat_id}",
        json.dumps({"text": chat_request.message, "role": "user"}),
    )
    await redis.rpush(
        f"chat_history:{chat_request.chat_id}",
        json.dumps({"text": response.json()["response"], "role": "assistant"}),
    )
    response_text = response.json()["response"]

    update_tokens_in(len(chat_request.message.split()))
    update_tokens_out(len(response_text.split()))

    return ChatResponse(response=response_text)


@router.get("/chat/{chat_id}/history", dependencies=[Depends(verify_token)])
async def get_chat_history(chat_id: str):
    """
    Retrieves the chat history for the given chat_id from Redis.

    :param chat_id: The ID of the chat to retrieve history for
    :type chat_id: str
    :return: A dictionary containing the chat_id and its history
    :rtype: dict
    :raises HTTPException: If chat history is not found
    """
    chat_history = await redis.lrange(f"chat_history:{chat_id}", 0, -1)
    if not chat_history:
        raise HTTPException(status_code=404, detail="Chat history not found")

    decoded_history = [msg.decode() for msg in chat_history]
    return {"chat_id": chat_id, "history": decoded_history}
