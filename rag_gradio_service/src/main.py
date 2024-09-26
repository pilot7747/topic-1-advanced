import logging

import gradio as gr
import httpx
from config import OPENAI_MODEL, template_html

# unofficial hack
from gradio_modal import Modal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

credentials = {}


def get_id_from_req(request: gr.Request) -> str:
    headers = request.request.headers.get("user-agent")
    ip = request.request.client.host

    return ip + headers


def add_text(history: list[list], text: str) -> tuple[list[list], gr.Textbox]:
    history = [] if history is None else history
    history = history + [[text, None]]
    return history, gr.Textbox(value="", interactive=False)


async def generate(prompt: str, user_id: str) -> str:
    """
    Generate given prompt and user_id
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"http://gateway_service:8001/chat/",
                json={
                    "message": prompt,
                    "model": OPENAI_MODEL,
                    "chat_id": credentials[user_id]["chat_id"],
                },
                headers={"Authorization": credentials[user_id]["token"]},
                timeout=httpx.Timeout(60.0),
            )
        except httpx.ConnectError:
            raise gr.Error("Failed to connect to chat service")

    if response.status_code != 200:
        raise gr.Error(response.json()["detail"])

    credentials[user_id]["chat_id"] = response.json()["chat_id"]
    resp_message = response.json()["response"]

    return resp_message


async def bot(history: list[list], use_reranker: bool, request: gr.Request):
    if not history or not history[-1][0]:
        raise gr.Warning("The request is empty, please type something in")

    query = history[-1][0]

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://rag_service:8000/prompt_w_context/",
                json={"query": query, "use_reranker": use_reranker},
                timeout=httpx.Timeout(60.0),
            )
        except httpx.ConnectError:
            raise gr.Error("Failed to connect to RAG service")

    if response.status_code != 200:
        raise gr.Error(response.json()["detail"])

    prompt_html = template_html.render(
        documents=response.json()["context"], query=query
    )
    resp_message = await generate(
        prompt=response.json()["message"], user_id=get_id_from_req(request)
    )
    history[-1][1] = resp_message

    return history, prompt_html


async def api_key_auth(token: str, request: gr.Request):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://gateway_service:8001/verify_token/",
                headers={"Authorization": token},
                timeout=httpx.Timeout(60.0),
            )
        except httpx.ConnectError:
            raise gr.Error("Failed to connect to verification service")

    if response.status_code != 200:
        raise gr.Error(response.json()["detail"])

    credentials[get_id_from_req(request)] = {"token": token, "chat_id": None}

    return Modal(visible=False)


with gr.Blocks() as demo:
    # blocking pop-up
    with Modal(visible=True, allow_user_close=False) as modal:
        token = gr.Textbox(label="Provide your token:")
        submit_token = gr.Button(value="Submit")

    submit_token.click(api_key_auth, [token], [modal])

    chatbot = gr.Chatbot(
        [],
        elem_id="chatbot",
        avatar_images=(
            "https://aui.atlassian.com/aui/8.8/docs/images/avatar-person.svg",
            "https://huggingface.co/datasets/huggingface/brand-assets/resolve/main/hf-logo.svg",
        ),
        bubble_full_width=False,
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
        bot, [chatbot, cb], [chatbot, prompt_html]
    )
    # Turn it back on
    txt_msg.then(lambda: gr.Textbox(interactive=True), None, [txt], queue=False)
    # Turn off interactivity while generating if you hit enter
    txt_msg = txt.submit(add_text, [chatbot, txt], [chatbot, txt], queue=False).then(
        bot, [chatbot, cb], [chatbot, prompt_html]
    )
    # Turn it back on
    txt_msg.then(lambda: gr.Textbox(interactive=True), None, [txt], queue=False)


demo.queue()
demo.launch(debug=True)
