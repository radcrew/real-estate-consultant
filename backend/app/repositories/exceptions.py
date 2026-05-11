"""HTTP errors raised by repository helpers."""

from __future__ import annotations

from collections.abc import Iterable
from typing import NoReturn

from fastapi import status
from supabase import AuthApiError

from app.utils.exceptions import (
    raise_bad_gateway,
    raise_client_error,
    raise_conflict,
    raise_forbidden,
    raise_not_found,
    raise_service_unavailable,
    raise_unauthorized,
    raise_unprocessable_entity,
)


def _weak_password_detail(message: str, reasons: Iterable[str] | None) -> str:
    base = (message or "Password does not meet requirements.").strip()
    if not reasons:
        return base
    parts = [str(r).strip() for r in reasons if str(r).strip()]
    if not parts:
        return base
    return f"{base} ({'; '.join(parts)})"


def raise_admin_auth_api_error(exc: AuthApiError) -> NoReturn:
    """Typical GoTrue errors when updating a user via the admin API."""
    if exc.code in ("email_exists", "user_already_exists", "phone_exists"):
        raise_conflict("That email or phone is already in use.", cause=exc)
    if exc.code in ("email_not_confirmed", "provider_email_needs_verification"):
        raise_forbidden(str(exc.message), cause=exc)
    status_code = exc.status if 400 <= exc.status < 600 else status.HTTP_400_BAD_REQUEST
    raise_client_error(status_code, str(exc.message), cause=exc)


def raise_weak_password(
    *,
    message: str,
    reasons: Iterable[str] | None = None,
    cause: BaseException,
) -> NoReturn:
    """422 when Supabase rejects the password; response ``detail`` is a single string."""
    raise_unprocessable_entity(_weak_password_detail(message, reasons), cause=cause)


def raise_could_not_load_profile(*, cause: BaseException | None = None) -> NoReturn:
    raise_service_unavailable("Could not load profile.", cause=cause)


def raise_profile_service_unavailable(*, cause: BaseException | None = None) -> NoReturn:
    raise_service_unavailable(
        "Profile service is temporarily unavailable.",
        cause=cause,
    )


def raise_current_password_incorrect(*, cause: BaseException | None = None) -> NoReturn:
    raise_unauthorized("Current password is incorrect.", cause=cause)


def raise_password_verification_unavailable(*, cause: BaseException | None = None) -> NoReturn:
    raise_service_unavailable(
        "Could not verify password. Try again later.",
        cause=cause,
    )


def raise_password_auth_transport_unavailable(*, cause: BaseException | None = None) -> NoReturn:
    raise_service_unavailable(
        "Authentication service is temporarily unavailable.",
        cause=cause,
    )


def raise_intake_session_not_found() -> NoReturn:
    raise_not_found("Intake session not found.")


def raise_intake_questions_load_empty() -> NoReturn:
    raise_bad_gateway("No question is configured for intake flow.")
