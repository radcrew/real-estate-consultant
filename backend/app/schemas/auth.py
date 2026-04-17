from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EmailPasswordRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class SignUpRequest(EmailPasswordRequest):
    pass


class SignInRequest(EmailPasswordRequest):
    pass


class SignUpResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str | None
    created_at: datetime


class SignInUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str | None


class SignInResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str
    user: SignInUser
