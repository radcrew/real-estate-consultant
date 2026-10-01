"""HTTP errors for public auth endpoints."""

from __future__ import annotations

from typing import NoReturn

from botocore.exceptions import ClientError
from fastapi import status

from app.utils.exceptions import (
    raise_client_error,
    raise_conflict,
    raise_forbidden,
    raise_service_unavailable,
    raise_too_many_requests,
    raise_unauthorized,
    raise_unprocessable_entity,
)
from supabase import AuthApiError


def raise_sign_in_invalid_credentials(*, cause: BaseException) -> NoReturn:
    raise_unauthorized("Invalid email or password.", cause=cause)


def raise_sign_in_email_not_confirmed(*, message: str, cause: AuthApiError) -> NoReturn:
    raise_forbidden(message, cause=cause)


def raise_auth_api_error(exc: AuthApiError) -> NoReturn:
    status_code = exc.status if 400 <= exc.status < 600 else status.HTTP_400_BAD_REQUEST
    raise_client_error(status_code, str(exc.message), cause=exc)


def raise_sign_in_transport_unavailable(*, cause: BaseException) -> NoReturn:
    raise_service_unavailable(
        "Authentication service is temporarily unavailable. Please try again.",
        cause=cause,
    )


def raise_sign_in_no_session() -> NoReturn:
    raise_forbidden(
        "No session returned. Confirm your email if your project requires it.",
    )


def raise_sign_up_email_already_exists(*, cause: BaseException) -> NoReturn:
    raise_conflict("An account with this email already exists.", cause=cause)


def raise_invalid_verification_code(*, cause: BaseException) -> NoReturn:
    raise_client_error(status.HTTP_400_BAD_REQUEST, "Invalid verification code.", cause=cause)


def raise_verification_code_expired(*, cause: BaseException) -> NoReturn:
    raise_client_error(
        status.HTTP_400_BAD_REQUEST,
        "Verification code has expired. Request a new one.",
        cause=cause,
    )


def cognito_error_code(exc: ClientError) -> str:
    return exc.response.get("Error", {}).get("Code", "")


def raise_cognito_error(exc: ClientError) -> NoReturn:
    """Fallback for Cognito errors an endpoint does not map itself."""
    code = cognito_error_code(exc)
    message = exc.response.get("Error", {}).get("Message") or "Authentication request failed."
    if code == "InvalidPasswordException":
        raise_unprocessable_entity(message, cause=exc)
    if code in ("TooManyRequestsException", "LimitExceededException"):
        raise_too_many_requests("Too many attempts. Please wait and try again.", cause=exc)
    if code == "InternalErrorException":
        raise_sign_in_transport_unavailable(cause=exc)
    raise_client_error(status.HTTP_400_BAD_REQUEST, message, cause=exc)
