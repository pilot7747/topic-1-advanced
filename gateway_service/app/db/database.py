import asyncio

from app.core.config import DATABASE_URL
from databases import Database
from redis import asyncio as aioredis
from sqlalchemy import MetaData

database = Database(DATABASE_URL)
async def connect_db():
    await database.connect()
asyncio.run(connect_db())
metadata = MetaData()
redis = aioredis.from_url("redis://redis:6379")
