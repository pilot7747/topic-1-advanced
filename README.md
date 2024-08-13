# Simple Generation Service

## Architecture
1. The user sends the request to our *platform* — `middleware_service` (maybe rename to platform or gateway?) which then forwards the request to `chat_service`.
2. `chat_service` is a simple service which only job is to generate responses to prompt chats.

## Running the Platform
We use Poetry and Python 3.11. To run services locally, install them with `poetry install` in a corresponding directory.

```bash
docker-compose up --buil
```

Test
