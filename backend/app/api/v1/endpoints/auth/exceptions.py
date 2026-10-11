"""HTTP errors for public auth endpoints."""

from __future__ import annotations

from typing import NoReturn

from botocore.exceptions import ClientError
from fastapi import status

from app.core.exceptions import raise_auth_invalid_access_token
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


def raise_oauth_code_rejected(*, cause: BaseException) -> NoReturn:
    raise_client_error(
        status.HTTP_400_BAD_REQUEST,
        "Google sign-in could not be completed. Please try again.",
        cause=cause,
    )


# Detail the frontend's /auth/callback matches to restart Google sign-in once.
OAUTH_ACCOUNT_LINKED = "account_linked"


def raise_oauth_account_linked() -> NoReturn:
    """The Google identity was just linked to an existing account; sign in again."""
    raise_conflict(OAUTH_ACCOUNT_LINKED)


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


def lacks_admin_scope(exc: ClientError) -> bool:
    """Tokens from Google sign-in lack aws.cognito.signin.user.admin, which the
    self-service calls (GetUser, UpdateUserAttributes, ChangePassword) require."""
    return cognito_error_code(exc) == "NotAuthorizedException" and "scope" in str(exc).lower()


def access_token_rejected(exc: ClientError) -> bool:
    """Cognito refused the access token itself: revoked by a sign-out, expired, or invalid.

    Our own check only verifies the signature and expiry, so a revoked token gets this far.
    """
    return (
        cognito_error_code(exc) == "NotAuthorizedException"
        and "access token" in str(exc).lower()
        and not lacks_admin_scope(exc)
    )


def raise_cognito_error(exc: ClientError) -> NoReturn:
    """Fallback for Cognito errors an endpoint does not map itself."""
    code = cognito_error_code(exc)
    message = exc.response.get("Error", {}).get("Message") or "Authentication request failed."
    if access_token_rejected(exc):
        # 401, so the browser refreshes the session or sends the user to sign in.
        raise_auth_invalid_access_token(cause=exc)
    if code == "InvalidPasswordException":
        raise_unprocessable_entity(message, cause=exc)
    if code in ("TooManyRequestsException", "LimitExceededException"):
        raise_too_many_requests("Too many attempts. Please wait and try again.", cause=exc)
    if code == "InternalErrorException":
        raise_sign_in_transport_unavailable(cause=exc)
    raise_client_error(status.HTTP_400_BAD_REQUEST, message, cause=exc)
