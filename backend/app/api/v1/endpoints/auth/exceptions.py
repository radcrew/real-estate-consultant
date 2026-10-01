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


def raise_sign_in_invalid_credentials(*, cause: BaseException) -> NoReturn:
    raise_unauthorized("Invalid email or password.", cause=cause)


def raise_refresh_token_rejected(*, cause: BaseException) -> NoReturn:
    raise_unauthorized("Session expired. Please sign in again.", cause=cause)


def raise_sign_in_email_not_confirmed(*, cause: BaseException) -> NoReturn:
    raise_forbidden("Confirm your email address before signing in.", cause=cause)


def raise_sign_in_transport_unavailable(*, cause: BaseException) -> NoReturn:
    raise_service_unavailable(
        "Authentication service is temporarily unavailable. Please try again.",
        cause=cause,
    )


def raise_sign_in_challenge_required(challenge: str | None) -> NoReturn:
    """Cognito wants another step (new password, MFA, ...) that this app does not support."""
    raise_forbidden(f"Sign-in requires an additional step ({challenge or 'unknown'}).")


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
