import os

# from https://stackoverflow.com/questions/31249112/allow-docker-container-to-connect-to-a-local-host-postgres-database
DATABASE_URL = "postgresql://chief:password@docker.for.mac.host.internal:5432/postgres" #"postgresql://chief:password@localhost:5432/postgres" #"postgresql://chief:password@docker.for.mac.host.internal:5432/postgres"
ADMIN_TOKEN = os.getenv("ADMIN_KEY")
RATE_LIMIT = 5  # max requests per minute
RATE_LIMIT_KEY_PREFIX = "rate_limit"
INFERENCE_ROUTING = {"gpt-4o-mini": "gpt-4-mini", "gpt-4o": "gpt-4o"}
