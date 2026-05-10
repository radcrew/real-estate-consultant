"""HTTP errors for ``get_current_user`` (bearer token dependency)."""

from __future__ import annotations

from typing import NoReturn

from supabase import AuthApiError

from app.exceptions.common import raise_unauthorized

_WWW_BEARER = {"WWW-Authenticate": "Bearer"}


def raise_auth_missing_bearer() -> NoReturn:
    raise_unauthorized("Not authenticated", headers=_WWW_BEARER)


def raise_auth_invalid_access_token(*, cause: AuthApiError | None = None) -> NoReturn:
    raise_unauthorized(
        "Invalid or expired access token.",
        cause=cause,
        headers=_WWW_BEARER,
    )


def raise_auth_user_not_returned() -> NoReturn:
    raise_unauthorized("Invalid or expired access token.", headers=_WWW_BEARER)
