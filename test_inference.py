import requests
import os


if __name__ == "__main__":
    base_url = os.environ.get("INFERENCE_URL", "http://127.0.0.1:8000")
    url = base_url + "/chat"

    chat_history = []
    simple_json = {
        "message": "Hello. What's new in London today?",
        "chat_history": chat_history
    }

    response = requests.post(url, json=simple_json).json()

    print(f"Answer:\n {response['response']}")
