from pydantic import BaseModel


class RAGRequest(BaseModel):
    query: str
    model: str = "gpt-4o"
    use_reranker: bool = True
    top_k_retrieve: int = 20
    top_k_rank: int = 4
    max_out_tokens: int = 512


class AddToDBRequest(BaseModel):
    text: str
    truncate: bool = True
