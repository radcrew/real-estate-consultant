"""HTTP errors for core dependencies."""

from __future__ import annotations

from typing import NoReturn

from app.utils.exceptions import raise_service_unavailable, raise_unauthorized

_WWW_BEARER = {"WWW-Authenticate": "Bearer"}


def raise_auth_missing_bearer() -> NoReturn:
    raise_unauthorized("Not authenticated", headers=_WWW_BEARER)


def raise_auth_invalid_access_token(*, cause: BaseException | None = None) -> NoReturn:
    raise_unauthorized(
        "Invalid or expired access token.",
        cause=cause,
        headers=_WWW_BEARER,
    )


def raise_auth_provider_unavailable(*, cause: BaseException) -> NoReturn:
    raise_service_unavailable(
        "Authentication service is temporarily unavailable. Please try again.",
        cause=cause,
    )
