from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    chat_id: str


class ChatResponse(BaseModel):
    response: str
