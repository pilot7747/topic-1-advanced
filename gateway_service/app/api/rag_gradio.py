import json
import logging
import gradio as gr
import httpx

from typing import AsyncGenerator
from fastapi import Request

from jinja2 import Environment, FileSystemLoader
from app.core.config import INFERENCE_ROUTING
from app.main import app
from app.api.chat import chat_proxy
from app.core.security import verify_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

env = Environment(loader=FileSystemLoader("../rag_template"))
template_html = env.get_template("template_html.j2")
state = {}

model_name = "gpt-4o"

def add_text(history: list[list], text: str) -> tuple[list[list], gr.Textbox]:
    history = [] if history is None else history
    history = history + [[text, None]]
    return history, gr.Textbox(value="", interactive=False)


async def generate(prompt: str):
    """
    Generate a sequence of tokens based on a given prompt and history using OpenAI API.
    History is not currently used
    """
    async with httpx.AsyncClient() as client:
        try:
            resp = await chat_proxy(message=prompt)
            return resp.response
        except Exception as e:
            raise gr.Error(str(e))


async def bot(history: list[list], use_ranker: bool):# -> AsyncGenerator[tuple[list[list], str], None]:
    if not history or not history[-1][0]:
        raise gr.Warning("The request is empty, please type something in")
    
    query = history[-1][0]

    async with httpx.AsyncClient() as client:
        try:
            rag_response = await client.post(
                "http://0.0.0.0:8004/prompt_w_context",
                json={
                    "query": query,
                    "use_ranker": use_ranker
                },
                timeout=httpx.Timeout(20.0),
            )
        except httpx.ConnectError:
            raise gr.Error("Failed to connect to RAG service")

    if rag_response.status_code != 200:
        raise gr.Error("RAG service error")

    rag_response = json.loads(rag_response.content)
    prompt_html = template_html.render(documents=rag_response["context"], query=query)

    return [generate(rag_response["message"])], prompt_html
    # history[-1][1] = ""
    # async for character in generate(rag_response["message"]):
    #     history[-1][1] = character
    #     yield history, prompt_html


with gr.Blocks() as demo:
    chatbot = gr.Chatbot(
        [],
        elem_id="chatbot",
        avatar_images=('https://aui.atlassian.com/aui/8.8/docs/images/avatar-person.svg',
                        'https://huggingface.co/datasets/huggingface/brand-assets/resolve/main/hf-logo.svg'),
        bubble_full_width=False
    )

    with gr.Row():
        txt = gr.Textbox(
            scale=3,
            show_label=False,
            placeholder="Enter text and press enter",
            container=False,
        )
        txt_btn = gr.Button(value="Submit text", scale=1)

    cb = gr.Checkbox(label="Use reranker", info="Rerank after retrieval?")

    prompt_html = gr.HTML()
    # Turn off interactivity while generating if you click
    txt_msg = txt_btn.click(add_text, [chatbot, txt], [chatbot, txt], queue=False).then(
        bot, [chatbot, cb], [chatbot, prompt_html])
    # Turn it back on
    txt_msg.then(lambda: gr.Textbox(interactive=True), None, [txt], queue=False)
    # Turn off interactivity while generating if you hit enter
    txt_msg = txt.submit(add_text, [chatbot, txt], [chatbot, txt], queue=False).then(
        bot, [chatbot, cb], [chatbot, prompt_html])
    # Turn it back on
    txt_msg.then(lambda: gr.Textbox(interactive=True), None, [txt], queue=False)


# demo.queue()
# demo.launch(debug=True, share=True)

def auth(request: Request):
    token = request.get("Authorization", None)
    return "A"
    # try:
    #     verify_token(token)
    #     return token
    # except:
    #     logger.error("Authentication failed")
    #     return None

app = gr.mount_gradio_app(app, demo, path="/rag_gradio", auth_dependency=auth)


import uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)