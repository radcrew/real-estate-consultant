"""Supabase Auth admin user I/O with consistent HTTP error mapping."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from supabase import AsyncClient, AuthApiError, AuthWeakPasswordError
from supabase_auth.types import User

from app.exceptions.admin_auth import raise_admin_auth_api_error
from app.exceptions.supabase import (
    raise_could_not_load_profile,
    raise_profile_service_unavailable,
    raise_weak_password,
)

logger = logging.getLogger(__name__)


async def admin_get_user(client: AsyncClient, user_id: str) -> User:
    """Load a user via the admin API; maps transport/auth failures to HTTP errors."""
    try:
        return (await client.auth.admin.get_user_by_id(user_id)).user
    except AuthApiError as exc:
        logger.warning("admin get_user_by_id failed: %s", exc)
        raise_could_not_load_profile(cause=exc)
    except httpx.HTTPError as exc:
        logger.warning("admin get_user_by_id HTTP error: %s", exc)
        raise_could_not_load_profile(cause=exc)


async def admin_update_user(
    client: AsyncClient,
    user_id: str,
    attributes: dict[str, Any],
) -> None:
    """Update auth user fields (e.g. email, phone) via the admin API."""
    try:
        await client.auth.admin.update_user_by_id(user_id, attributes)
    except AuthApiError as exc:
        raise_admin_auth_api_error(exc)
    except httpx.HTTPError as exc:
        logger.warning("admin update_user_by_id HTTP error: %s", exc)
        raise_profile_service_unavailable(cause=exc)


async def admin_update_user_password(
    client: AsyncClient,
    user_id: str,
    *,
    new_password: str,
) -> None:
    """Set password via the admin API; maps weak-password and other auth errors."""
    try:
        await client.auth.admin.update_user_by_id(user_id, {"password": new_password})
    except AuthWeakPasswordError as exc:
        raise_weak_password(
            message=str(exc.message),
            reasons=getattr(exc, "reasons", None),
            cause=exc,
        )
    except AuthApiError as exc:
        if exc.code == "weak_password":
            raise_weak_password(message=str(exc.message), cause=exc)
        raise_admin_auth_api_error(exc)
    except httpx.HTTPError as exc:
        logger.warning("admin update password HTTP error: %s", exc)
        raise_profile_service_unavailable(cause=exc)
