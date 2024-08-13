from sqlalchemy import Table, Column, String

from app.db.database import metadata

users = Table(
    "users",
    metadata,
    Column("username", String, primary_key=True),
    Column("hashed_password", String),
    Column("api_key", String, unique=True),
)
