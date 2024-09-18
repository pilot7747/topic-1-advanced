import lancedb
import pyarrow as pa

from transformers import AutoConfig

LANCE_DB = lancedb.connect(".lancedb")
EMB_MODEL = "BAAI/bge-small-en-v1.5" #os.getenv("EMB_MODEL")
EMBED_URL = "http://embed_service:8080/embed" #os.getenv("EMBED_URL") + "/embed"
RERANK_URL = "http://rerank_service:8081/rerank" #os.getenv("RERANK_URL") + "/rerank"

# based on https://blog.lancedb.com/benchmarking-lancedb-92b01032874a/
NPROBES = 40
REFINE_FACTOR = 50
BATCH_SIZE = 4

config = AutoConfig.from_pretrained(EMB_MODEL)
emb_dim = config.hidden_size
schema = pa.schema(
    [
        pa.field("vector", pa.list_(pa.float32(), emb_dim)),
        pa.field("text", pa.string()),
    ]
)

LANCE_TABLE = LANCE_DB.create_table("docs", schema=schema, exist_ok=True)

RAG_PROMPT = """Instructions: Use the following unique documents in the Context section to answer the Query at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.
Context:
---
{context}
---
Query: {query}"""


