import base64
import json
import uuid

import httpx
from app.core.config import INFERENCE_ROUTING
from app.core.metrics import update_tokens_in, update_tokens_out
from app.core.security import verify_token
from app.db.database import redis
from app.schemas.chat import ChatRequest, ChatResponse
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()


def generate_chat_id() -> str:
    """
    Generates a short, URL-safe, unique chat ID.

    This function generates a UUID, converts it to a string, encodes it using URL-safe base64 encoding,
    and takes the first 22 characters of the resulting string to create a compact, unique identifier.

    :returns: The chat ID
    :rtype: str
    """
    random_uuid = uuid.uuid4()
    uuid_str = str(random_uuid).replace("-", "")
    base64_encoded = base64.urlsafe_b64encode(uuid_str.encode())
    short_id = base64_encoded.decode("utf-8").rstrip("=")

    return short_id[:22]


@router.post("/chat/", dependencies=[Depends(verify_token)])
async def chat_proxy(chat_request: ChatRequest) -> ChatResponse:
    """
    Handles chat proxying requests by interacting with a chat service and storing chat history in Redis.

    :param chat_request: The request payload containing the chat ID and message.
    :type chat_request: ChatRequest
    :return: The response from the chat service encapsulated in a ChatResponse object.
    :rtype: ChatResponse
    """
    chat_id = chat_request.chat_id
    if chat_request.chat_id is not None:
        chat_history = await redis.lrange(f"chat_history:{chat_request.chat_id}", 0, -1)
        chat_history = [json.loads(msg.decode()) for msg in chat_history]
    else:
        chat_id = generate_chat_id()
        chat_history = []

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"http://{INFERENCE_ROUTING[chat_request.model]}:8000/chat/",
                json={"message": chat_request.message, "chat_history": chat_history},
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

    await redis.rpush(
        f"chat_history:{chat_id}",
        json.dumps({"text": chat_request.message, "role": "user"}),
    )
    await redis.rpush(
        f"chat_history:{chat_id}",
        json.dumps({"text": response.json()["response"], "role": "assistant"}),
    )
    response_text = response.json()["response"]

    update_tokens_in(len(chat_request.message.split()))
    update_tokens_out(len(response_text.split()))

    return ChatResponse(response=response_text, chat_id=chat_id)


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
