FROM python:3.11-slim
LABEL authors="Nikita Pavlichenko"

WORKDIR /middleware_service

RUN pip install poetry==1.8.3
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root

COPY app/ ./app
RUN poetry install --only main

CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
