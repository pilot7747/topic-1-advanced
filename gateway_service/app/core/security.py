from app.core.config import ADMIN_TOKEN
from app.db.database import database
from app.db.models import users
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from passlib.context import CryptContext
from sqlalchemy.sql import select

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    :param plain_password: The plain text password input by the user
    :type plain_password: str
    :param hashed_password: The stored hashed password for comparison
    :type hashed_password: str
    :return: True if the plain text password matches the hashed password, False otherwise
    :rtype: bool
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Generates a hash for a given password using a predefined password context.

    :param password: The plain text password to be hashed
    :type password: str
    :return: The hashed password
    :rtype: str
    """
    return pwd_context.hash(password)


async def check_token(api_key: str) -> bool:
    """
    Checks if the provided API key is valid.

    If the API key matches the ADMIN_TOKEN, it automatically returns True.
    Otherwise, it queries the database to check if the API key exists and is associated with a user.

    :param api_key:
        The API key to be validated.
    :type api_key: str

    :return:
        A boolean value. True if the API key is valid, otherwise False.
    :rtype: bool
    """
    if api_key != ADMIN_TOKEN:
        query = select(users).where(users.c.api_key == api_key)
        user = await database.fetch_one(query)
        return user is not None
    return True


async def verify_token(api_key: str = Security(api_key_header)) -> None:
    """
    Verifies the provided API key by checking if it is valid.

    :param api_key: The API key to be verified.
    :type api_key: str
    :raises HTTPException: If the API key is not provided or is invalid.
    """
    if not api_key:
        raise HTTPException(status_code=403, detail="Unauthorized")
    if not await check_token(api_key):
        raise HTTPException(status_code=403, detail="Unauthorized")
