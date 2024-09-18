FROM python:3.11-slim

# WORKDIR /app
RUN pip install poetry==1.8.3
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root
COPY src/ ./src
RUN poetry install --no-dev
WORKDIR /src

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
