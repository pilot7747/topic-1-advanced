import requests
from pydantic import BaseModel


docs = [
    "Hey how are you?",
    "Transformers is an open source library",
    "BERT is a transformer-only model by Google",
    "Bear is big and brown can eat you",
    "A nice red car is parked at the office",
    "Trains arrive at a train station and plains at an airport"
]
#
resp = requests.post(
    "http://0.0.0.0:8001/add_to_rag_db/",
    json={
        "text": "BERT is a transformer-only model by Google"
    },
    headers={"Authorization": "root"},
)

resp = requests.post(
    "http://0.0.0.0:8001/rag/",
    json={
        "query": "how",
        "model": "gpt-4o-mini",
        "use_reranker": True,
        # "prompt_token_limit": 800
    },
    headers={"Authorization": "j"},
)

resp = requests.get(
    "http://0.0.0.0:8001/reindex/",
    headers={"Authorization": "root"},
)

print(resp.content)