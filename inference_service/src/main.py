import os

import openai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

openai.api_key = os.getenv("OPENAI_API_KEY")


class Message(BaseModel):
    text: str
    role: str


class ChatRequest(BaseModel):
    message: str
    chat_history: list[Message]


class ChatResponse(BaseModel):
    response: str


@app.post("/chat/")
async def chat_gpt(chat_request: ChatRequest) -> ChatResponse:
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                *[
                    {"role": "user", "content": msg}
                    for msg in chat_request.chat_history
                ],
                {"role": "user", "content": chat_request.message},
            ],
        )
        return ChatResponse(response=response.choices[0].message["content"])
    except openai.OpenAIError as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")
