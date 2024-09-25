FROM python:3.11-slim

RUN pip install poetry==1.8.3
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root

COPY src/ ./rag_gradio_service
RUN poetry install --no-dev
WORKDIR /rag_gradio_service

ENV GRADIO_SERVER_NAME="0.0.0.0"

CMD ["poetry", "run", "gradio", "main.py"]