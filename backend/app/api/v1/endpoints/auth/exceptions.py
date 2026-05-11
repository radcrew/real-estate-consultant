"""HTTP errors for public auth endpoints."""

from __future__ import annotations

from collections.abc import Iterable
from typing import NoReturn

from fastapi import status
from supabase import AuthApiError, AuthWeakPasswordError

from app.utils.exceptions import (
    raise_client_error,
    raise_conflict,
    raise_forbidden,
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


def raise_sign_in_invalid_credentials(*, cause: BaseException) -> NoReturn:
    raise_unauthorized("Invalid email or password.", cause=cause)


def raise_sign_in_email_not_confirmed(*, message: str, cause: AuthApiError) -> NoReturn:
    raise_forbidden(message, cause=cause)


def raise_sign_in_auth_api_error(exc: AuthApiError) -> NoReturn:
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


def raise_sign_up_auth_api_error(exc: AuthApiError) -> NoReturn:
    status_code = exc.status if 400 <= exc.status < 600 else status.HTTP_400_BAD_REQUEST
    raise_client_error(status_code, str(exc.message), cause=exc)


def raise_sign_up_weak_password_sdk(*, exc: AuthWeakPasswordError) -> NoReturn:
    raise_unprocessable_entity(
        _weak_password_detail(str(exc.message), getattr(exc, "reasons", None)),
        cause=exc,
    )


def raise_sign_up_weak_password_api(*, exc: AuthApiError) -> NoReturn:
    raise_unprocessable_entity(_weak_password_detail(str(exc.message), None), cause=exc)
