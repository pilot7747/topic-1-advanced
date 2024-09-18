curl -X 'POST' \
  'http://localhost:8000/chat/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "message": "What was my last message?",
  "chat_history": [
    {
      "text": "Hi!",
      "role": "user"
    }
  ]
}'
