from app.core.config import DATABASE_URL
from databases import Database
from redis import asyncio as aioredis
from sqlalchemy import MetaData

database = Database(DATABASE_URL)
metadata = MetaData()
redis = aioredis.from_url("redis://redis:6379")
