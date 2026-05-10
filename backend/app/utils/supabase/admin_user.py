"""Supabase Auth admin user I/O with consistent HTTP error mapping."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from fastapi import HTTPException, status
from supabase import AsyncClient, AuthApiError, AuthWeakPasswordError
from supabase_auth.types import User

from app.utils.supabase.admin_auth import http_exception_from_admin_auth_api_error

logger = logging.getLogger(__name__)

_LOAD_ACCOUNT_HTTP_DETAIL = "Profile service is temporarily unavailable."


async def admin_get_user(client: AsyncClient, user_id: str) -> User:
    """Load a user via the admin API; maps transport/auth failures to HTTP errors."""
    try:
        return (await client.auth.admin.get_user_by_id(user_id)).user
    except AuthApiError as exc:
        logger.warning("admin get_user_by_id failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not load profile.",
        ) from exc
    except httpx.HTTPError as exc:
        logger.warning("admin get_user_by_id HTTP error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not load profile.",
        ) from exc


async def admin_update_user(
    client: AsyncClient,
    user_id: str,
    attributes: dict[str, Any],
) -> None:
    """Update auth user fields (e.g. email, phone) via the admin API."""
    try:
        await client.auth.admin.update_user_by_id(user_id, attributes)
    except AuthApiError as exc:
        raise http_exception_from_admin_auth_api_error(exc) from exc
    except httpx.HTTPError as exc:
        logger.warning("admin update_user_by_id HTTP error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_LOAD_ACCOUNT_HTTP_DETAIL,
        ) from exc


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
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": exc.message, "reasons": exc.reasons},
        ) from exc
    except AuthApiError as exc:
        if exc.code == "weak_password":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=exc.message,
            ) from exc
        raise http_exception_from_admin_auth_api_error(exc) from exc
    except httpx.HTTPError as exc:
        logger.warning("admin update password HTTP error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_LOAD_ACCOUNT_HTTP_DETAIL,
        ) from exc
