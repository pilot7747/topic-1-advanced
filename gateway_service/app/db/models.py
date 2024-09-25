from app.db.database import metadata
from sqlalchemy import Column, String, Table

users = Table(
    "users",
    metadata,
    Column("username", String, primary_key=True),
    Column("hashed_password", String),
    Column("api_key", String, unique=True),
)
