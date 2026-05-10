"""Semantic HTTP errors for Supabase Auth / account flows (callers log; helpers only raise)."""

from __future__ import annotations

from collections.abc import Iterable
from typing import NoReturn

from fastapi import status

from app.core.exceptions import raise_http_exception


def _weak_password_detail(message: str, reasons: Iterable[str] | None) -> str:
    base = (message or "Password does not meet requirements.").strip()
    if not reasons:
        return base
    parts = [str(r).strip() for r in reasons if str(r).strip()]
    if not parts:
        return base
    return f"{base} ({'; '.join(parts)})"


def raise_weak_password(
    *,
    message: str,
    reasons: Iterable[str] | None = None,
    cause: BaseException,
) -> NoReturn:
    """422 when Supabase rejects the password; response ``detail`` is a single string."""
    raise_http_exception(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        _weak_password_detail(message, reasons),
        cause=cause,
    )


def raise_could_not_load_profile(*, cause: BaseException | None = None) -> NoReturn:
    raise_http_exception(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "Could not load profile.",
        cause=cause,
    )


def raise_profile_service_unavailable(*, cause: BaseException | None = None) -> NoReturn:
    raise_http_exception(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "Profile service is temporarily unavailable.",
        cause=cause,
    )


def raise_password_change_not_configured() -> NoReturn:
    raise_http_exception(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "Password change is not configured (set SUPABASE_ANON_KEY on the API).",
    )


def raise_current_password_incorrect(*, cause: BaseException | None = None) -> NoReturn:
    raise_http_exception(
        status.HTTP_401_UNAUTHORIZED,
        "Current password is incorrect.",
        cause=cause,
    )


def raise_password_verification_unavailable(*, cause: BaseException | None = None) -> NoReturn:
    raise_http_exception(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "Could not verify password. Try again later.",
        cause=cause,
    )


def raise_password_auth_transport_unavailable(*, cause: BaseException | None = None) -> NoReturn:
    raise_http_exception(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "Authentication service is temporarily unavailable.",
        cause=cause,
    )
