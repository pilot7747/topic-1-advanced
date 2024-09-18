import requests

docs = [
    "Hey how are you?",
    "Transformers is an open source library",
    "BERT is a transformer-only model by Google",
    "Bear is big and brown can eat you",
    "A nice red car is parked at the office",
    "Trains arrive at a train station and plains at an airport"
]

# for doc in docs:
#     resp = requests.post(
#         "http://0.0.0.0:8000/add_to_rag_db",
#         json={
#             "text": doc
#         }
#     )

resp = requests.post(
    "http://0.0.0.0:8000/prompt_w_context",
    json={
        "query": "how",
        "use_reranker": False,
        "prompt_token_limit": 800
    }
)
if resp.status_code == 500:
    print("status 500")
else:
    print(resp.content)