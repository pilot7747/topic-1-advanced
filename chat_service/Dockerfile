FROM python:3.11-slim
LABEL authors="Nikita Pavlichenko"

WORKDIR /app
RUN pip install poetry==1.8.3
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root
COPY src/ ./src
RUN poetry install --no-dev


CMD ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
