"""Forgotten password: email a code, then set a new password with it."""

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Response, status

from app.api.v1.endpoints.auth.exceptions import (
    cognito_error_code,
    raise_cognito_error,
    raise_invalid_verification_code,
    raise_sign_in_transport_unavailable,
    raise_verification_code_expired,
)
from app.core.cognito import call_idp, secret_hash
from app.core.config import settings
from app.schemas.auth import ForgotPasswordRequest, ResetPasswordRequest

router = APIRouter()


@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
async def forgot_password(body: ForgotPasswordRequest) -> Response:
    email = str(body.email)
    try:
        await call_idp(
            "forgot_password",
            ClientId=settings.cognito_client_id,
            SecretHash=secret_hash(email),
            Username=email,
        )

    except ClientError as exc:
        # Answer the same whether or not the account exists.
        if cognito_error_code(exc) != "UserNotFoundException":
            raise_cognito_error(exc)

    except BotoCoreError as exc:
        raise_sign_in_transport_unavailable(cause=exc)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(body: ResetPasswordRequest) -> Response:
    email = str(body.email)
    try:
        await call_idp(
            "confirm_forgot_password",
            ClientId=settings.cognito_client_id,
            SecretHash=secret_hash(email),
            Username=email,
            ConfirmationCode=body.code.strip(),
            Password=body.password,
        )

    except ClientError as exc:
        code = cognito_error_code(exc)
        # An unknown email reads as a bad code, for the same reason as above.
        if code in ("CodeMismatchException", "UserNotFoundException"):
            raise_invalid_verification_code(cause=exc)
        if code == "ExpiredCodeException":
            raise_verification_code_expired(cause=exc)
        raise_cognito_error(exc)

    except BotoCoreError as exc:
        raise_sign_in_transport_unavailable(cause=exc)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
