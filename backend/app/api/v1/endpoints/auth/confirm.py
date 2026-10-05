"""Email verification after sign-up: submit the emailed code, or ask for a new one."""

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
from app.core.deps import DbSession
from app.schemas.auth import ConfirmSignUpRequest, ResendCodeRequest
from app.services.google_user_merge import merge_google_user

router = APIRouter()


@router.post("/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def confirm_sign_up(body: ConfirmSignUpRequest, session: DbSession) -> Response:
    email = str(body.email)
    try:
        await call_idp(
            "confirm_sign_up",
            ClientId=settings.cognito_client_id,
            SecretHash=secret_hash(email),
            Username=email,
            ConfirmationCode=body.code.strip(),
        )

    except ClientError as exc:
        code = cognito_error_code(exc)
        if code == "CodeMismatchException":
            raise_invalid_verification_code(cause=exc)
        if code == "ExpiredCodeException":
            raise_verification_code_expired(cause=exc)
        raise_cognito_error(exc)

    except BotoCoreError as exc:
        raise_sign_in_transport_unavailable(cause=exc)

    # The code proved this person owns the email, so a Google-only user with the same
    # address can now be folded into this account. Failures are logged, never raised.
    await merge_google_user(session, email)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/resend-code", status_code=status.HTTP_204_NO_CONTENT)
async def resend_code(body: ResendCodeRequest) -> Response:
    email = str(body.email)
    try:
        await call_idp(
            "resend_confirmation_code",
            ClientId=settings.cognito_client_id,
            SecretHash=secret_hash(email),
            Username=email,
        )

    except ClientError as exc:
        raise_cognito_error(exc)

    except BotoCoreError as exc:
        raise_sign_in_transport_unavailable(cause=exc)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
