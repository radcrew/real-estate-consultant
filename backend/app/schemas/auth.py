from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EmailPasswordRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class SignUpRequest(EmailPasswordRequest):
    first_name: str = Field(min_length=1, max_length=120)
    last_name: str = Field(min_length=1, max_length=120)


class SignInRequest(EmailPasswordRequest):
    pass


class ResendCodeRequest(BaseModel):
    email: EmailStr


class ConfirmSignUpRequest(ResendCodeRequest):
    code: str = Field(min_length=1, max_length=20)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(EmailPasswordRequest):
    """``password`` is the new password; ``code`` is the one emailed by forgot-password."""

    code: str = Field(min_length=1, max_length=20)


class OAuthExchangeRequest(BaseModel):
    code: str = Field(min_length=1, max_length=2048)
    # Must equal the redirect_uri sent to /oauth2/authorize; Cognito checks both.
    redirect_uri: str = Field(min_length=1, max_length=2048)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)
    # SignInUser.username from the original sign-in.
    username: str = Field(min_length=1, max_length=128)


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
    # Cognito user name; the client sends it back to /auth/refresh.
    username: str


class SignInResponse(BaseModel):
    access_token: str
    id_token: str
    refresh_token: str
    expires_in: int
    token_type: str
    user: SignInUser
