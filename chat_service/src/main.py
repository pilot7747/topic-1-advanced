from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
import httpx

app = FastAPI()

openai.api_key = "your_openai_api_key"


class Message(BaseModel):
    text: str
    role: str


class ChatRequest(BaseModel):
    message: str
    chat_history: list[Message]


@app.post("/chat/")
async def chat_gpt(chat_request: ChatRequest):
    try:
        # response = openai.ChatCompletion.create(
        #     model="gpt-4",
        #     messages=[
        #         {"role": "system", "content": "You are a helpful assistant."},
        #         *[
        #             {"role": "user", "content": msg}
        #             for msg in chat_request.chat_history
        #         ],
        #         {"role": "user", "content": chat_request.message},
        #     ],
        # )
        # return {"response": response.choices[0].message["content"]}
        return {"response": "Hello!"}
    except openai.error.OpenAIError as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")
