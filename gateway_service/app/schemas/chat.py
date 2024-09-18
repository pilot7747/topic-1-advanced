from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    model: str
    stream: bool = False
    chat_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    chat_id: str
