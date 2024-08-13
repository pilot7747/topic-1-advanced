from pydantic import BaseModel


class SignupResponse(BaseModel):
    message: str
    api_key: str
