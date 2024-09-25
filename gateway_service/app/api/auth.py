from app.core.security import get_password_hash
from app.db.database import database
from app.db.models import users
from app.schemas.signup import SignupResponse
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.sql import insert, select

router = APIRouter()


@router.post("/signup/")
async def signup(form_data: OAuth2PasswordRequestForm = Depends()) -> SignupResponse:
    """
    Handles user signup by creating a new user in the database with a hashed password and generating an API key.

    :param form_data: Form data containing the username and password for signup.
    :type form_data: OAuth2PasswordRequestForm
    :return: Response indicating successful user creation and the generated API key.
    :rtype: SignupResponse
    """
    query = select(users).where(users.c.username == form_data.username)
    user = await database.fetch_one(query)

    if user:
        raise HTTPException(status_code=400, detail="Username already taken")

    hashed_password = get_password_hash(form_data.password)
    api_key = "token" + str(hash(form_data.username))  # Simple token generation

    query = insert(users).values(
        username=form_data.username,
        hashed_password=hashed_password,
        api_key=api_key,
    )
    await database.execute(query)

    return SignupResponse(message="User created successfully.", api_key=api_key)
