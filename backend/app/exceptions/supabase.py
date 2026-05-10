"""Semantic HTTP errors for Supabase Auth / account flows (callers log; helpers only raise)."""

from __future__ import annotations

from collections.abc import Iterable
from typing import NoReturn

from app.exceptions.common import (
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


def raise_password_change_not_configured() -> NoReturn:
    raise_service_unavailable(
        "Password change is not configured (set SUPABASE_ANON_KEY on the API).",
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
