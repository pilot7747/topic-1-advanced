import logging
import gradio as gr
import httpx
import json

# unofficial hack
from gradio_modal import Modal

from config import template_html, OPENAI_MODEL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

credentials = {}

def add_text(history: list[list], text: str) -> tuple[list[list], gr.Textbox]:
    history = [] if history is None else history
    history = history + [[text, None]]
    return history, gr.Textbox(value="", interactive=False)


async def generate(prompt: str):
    """
    Generate a sequence of tokens based on a given prompt and history using OpenAI API.
    History is not currently used
    """
    headers = {"Authorization": f"Bearer: {credentials[request.username]}"}

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"http://{OPENAI_MODEL}:8000/chat/",
                json={"message": prompt},
                headers=headers,
                timeout=httpx.Timeout(20.0),
            )
        except httpx.ConnectError:
            raise gr.Error("Failed to connect to chat service")

    if resp.status_code != 200:
        raise gr.Error("RAG service error")

    res = json.loads(resp.content)["response"]
    return res


async def bot(history: list[list], use_reranker: bool, request: gr.Request):
    if not history or not history[-1][0]:
        raise gr.Warning("The request is empty, please type something in")

    query = history[-1][0]

    async with httpx.AsyncClient() as client:
        try:
            rag_response = await client.post(
                f"http://0.0.0.0:8004/prompt_w_context/",
                json={"query": query, "use_reranker": use_reranker},
                timeout=httpx.Timeout(20.0),
            )
        except httpx.ConnectError:
            raise gr.Error("Failed to connect to chat service")

    if rag_response.status_code != 200:
        raise gr.Error("RAG service error")

    rag_response = rag_response.json()
    prompt_html = template_html.render(documents=rag_response["context"], query=query)

    history[-1][1] = ""
    return generate(rag_response["message"]), prompt_html


async def api_key_auth(token, request: gr.Request):
    headers = request.request.headers.get("user-agent")
    ip = f"{request.request.client.host}:{request.request.client.port}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"http://0.0.0.0:8000/verify/token",
                headers={"Authorization": token},
                timeout=httpx.Timeout(20.0),
            )
        except httpx.ConnectError:
            raise gr.Error("Failed to connect to verification service")

    if response.status_code == 403:
        raise gr.Error("Authorization error")
    elif response.status_code != 200:
        raise gr.Error("Gateway service error")

    if token:
        credentials[ip + headers] = token
        return Modal(visible=False)

    raise gr.Warning("Token is not valid")
    # return Modal(visible=True)


with gr.Blocks() as demo:
    with Modal(
        visible=True,
        allow_user_close=False
    ) as modal:
        token = gr.Textbox(label="Provide your token:")
        submit_token = gr.Button(value="Submit")
    submit_token.click(api_key_auth, [token], [modal])

    chatbot = gr.Chatbot(
        [],
        elem_id="chatbot",
        avatar_images=('https://aui.atlassian.com/aui/8.8/docs/images/avatar-person.svg',
                       'https://huggingface.co/datasets/huggingface/brand-assets/resolve/main/hf-logo.svg'),
        bubble_full_width=False,
        show_copy_button=True,
        show_share_button=True,
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



demo.queue()
demo.launch(debug=True)
