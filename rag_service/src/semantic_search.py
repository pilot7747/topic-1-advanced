import logging
import json
import numpy as np
import httpx
from fastapi import HTTPException

from config import (
    RERANK_URL,
    EMBED_URL,
    LANCE_TABLE,
    REFINE_FACTOR,
    NPROBES,
    BATCH_SIZE
)

# Setting up the logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def retrieve(query: str, k: int) -> list[str]:
    """
    Retrieve top k items with RETRIEVER
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                EMBED_URL,
                json={
                    "inputs": query,
                    "truncate": True
                },
                timeout=httpx.Timeout(20.0)
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=500, detail="Failed to connect to TEI embed service"
            )
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code, detail="TEI embed service error"
        )
    query_vec = json.loads(response.content)[0]
    
    documents = LANCE_TABLE.search(
        query=query_vec
    ).nprobes(NPROBES).refine_factor(REFINE_FACTOR).limit(k).to_list()
    documents = [doc["text"] for doc in documents]

    if len(documents) == 0:
        logger.warning("The document table is empty")

    return documents


async def rerank(query: str, documents: list[str], k: int) -> list[str]:
    """
    Rerank items returned by RETRIEVER and return top k
    """
    scores = []
    for i in range(int(np.ceil(len(documents) / BATCH_SIZE))):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    RERANK_URL,
                    json={
                        "query": query,
                        "texts": documents[i * BATCH_SIZE:(i + 1) * BATCH_SIZE],
                        "truncate": True
                    },
                    timeout=httpx.Timeout(20.0)
                )
            except httpx.ConnectError:
                raise HTTPException(
                    status_code=500, detail="Failed to connect to TEI embed service"
                )
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code, detail="TEI embed service error"
            )
        batch_scores = json.loads(response.content)
        batch_scores = [s["score"] for s in batch_scores]
        scores.extend(batch_scores)

    documents = [doc for _, doc in sorted(zip(scores, documents))[-k:]]

    return documents