from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EmailPasswordRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class SignUpRequest(EmailPasswordRequest):
    first_name: str = Field(min_length=1, max_length=120)
    last_name: str = Field(min_length=1, max_length=120)


class SignInRequest(EmailPasswordRequest):
    pass


class SignUpResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str | None
    # True until the emailed code is submitted to /auth/confirm.
    confirmation_required: bool


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
