import os

DATABASE_URL = "postgresql://user:password@postgres/dbname"
ADMIN_TOKEN = os.getenv("ADMIN_KEY")
RATE_LIMIT = 5  # max requests per minute
RATE_LIMIT_KEY_PREFIX = "rate_limit"
