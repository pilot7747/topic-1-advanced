import json
import logging
import tiktoken
import httpx
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException

from semantic_search import rerank, retrieve
from config import LANCE_TABLE, EMBED_URL, RAG_PROMPT

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OAI_TOKENIZER = tiktoken.get_encoding("cl100k_base")


class RAGRequest(BaseModel):
    query: str
    use_reranker: bool = True
    top_k_retrieve: int = 20
    top_k_rank: int = 4
    prompt_token_limit: int = 2048
    max_out_tokens: int = 512


class RAGResponse(BaseModel):
    message: str
    context: list[str]


class AddToDBRequest(BaseModel):
    text: str
    truncate: True


def prepare_message(
        query: str,
        docs: list[str],
        prompt_token_limit: int,
        max_out_tokens: int
    ) -> (str, list[str]):
    """
    This is an attempt to truncate the context to the preset limit in order to keep the postfix
    """
    context = "\n".join(docs)
    message = RAG_PROMPT.format(context=context, query=query)

    while docs and len(OAI_TOKENIZER.encode(message)) > prompt_token_limit - max_out_tokens:
        docs.pop()
        context = "\n".join(docs)
        message = RAG_PROMPT.format(context=context, query=query)
        logger.warning(f"Context was reduced due to the token limit. "
                       f"Prompt was {len(OAI_TOKENIZER.encode(message))} tokens long")

    message = OAI_TOKENIZER.decode(
        OAI_TOKENIZER.encode(message)[:(prompt_token_limit - max_out_tokens)]
    )
    print(message)

    return message, docs


@app.post("/prompt_w_context/")
async def prompt_w_context(rag_request: RAGRequest):
    if rag_request.use_reranker:
        retrieved_docs = await retrieve(rag_request.query, rag_request.top_k_retrieve)
        documents = await rerank(rag_request.query, retrieved_docs, rag_request.top_k_rank)
    else:
        documents = await retrieve(rag_request.query, rag_request.top_k_rank)

    message, documents = prepare_message(rag_request.query, documents,
        rag_request.prompt_token_limit,
        rag_request.max_out_tokens)

    resp = RAGResponse(message=message, context=documents)
    return resp


@app.post("/add_to_rag_db/")
async def add_to_db(add_to_db_request: AddToDBRequest):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                EMBED_URL,
                json=add_to_db_request.model_dump(),
                timeout=httpx.Timeout(20.0),
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=500, detail="Failed to connect to TEI service"
            )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code, detail="TEI service error"
        )
    vector = json.loads(response.content)[0]

    data = [
        {"vector": vector, "text": add_to_db_request.text}
    ]
    LANCE_TABLE.add(data=data)


@app.get("/reindex/")
async def reindex():
    LANCE_TABLE.create_index()


# import uvicorn
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8007)