import os

DATABASE_URL = "postgresql://chief:password@localhost/postgres"
ADMIN_TOKEN = "admin_key" #os.getenv("ADMIN_KEY")
RATE_LIMIT = 5  # max requests per minute
RATE_LIMIT_KEY_PREFIX = "rate_limit"
INFERENCE_ROUTING = {"gpt-4o-mini": "gpt-4-mini", "gpt-4o": "gpt-4o"}
