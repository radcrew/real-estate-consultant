"""HTTP errors raised by repository helpers."""

from __future__ import annotations

from typing import NoReturn

from fastapi import status

from app.utils.exceptions import (
    raise_bad_gateway,
    raise_client_error,
    raise_conflict,
    raise_forbidden,
    raise_not_found,
    raise_service_unavailable,
    raise_unauthorized,
)
from supabase import AuthApiError


def raise_admin_auth_api_error(exc: AuthApiError) -> NoReturn:
    """Typical GoTrue errors when updating a user via the admin API."""
    if exc.code in ("email_exists", "user_already_exists", "phone_exists"):
        raise_conflict("That email or phone is already in use.", cause=exc)
    if exc.code in ("email_not_confirmed", "provider_email_needs_verification"):
        raise_forbidden(str(exc.message), cause=exc)
    status_code = exc.status if 400 <= exc.status < 600 else status.HTTP_400_BAD_REQUEST
    raise_client_error(status_code, str(exc.message), cause=exc)


def raise_could_not_load_profile(*, cause: BaseException | None = None) -> NoReturn:
    raise_service_unavailable("Could not load profile.", cause=cause)


def raise_profile_service_unavailable(*, cause: BaseException | None = None) -> NoReturn:
    raise_service_unavailable(
        "Profile service is temporarily unavailable.",
        cause=cause,
    )


def raise_current_password_incorrect(*, cause: BaseException | None = None) -> NoReturn:
    raise_unauthorized("Current password is incorrect.", cause=cause)


def raise_intake_session_not_found() -> NoReturn:
    raise_not_found("Intake session not found.")


def raise_intake_job_not_found() -> NoReturn:
    """Unknown job, or one belonging to another session.

    Both cases answer the same way on purpose: a job id is a bearer token, and telling a
    caller that an id exists but is not theirs is itself a disclosure.
    """
    raise_not_found("Intake job not found.")


def raise_intake_questions_load_empty() -> NoReturn:
    raise_bad_gateway("No question is configured for intake flow.")
