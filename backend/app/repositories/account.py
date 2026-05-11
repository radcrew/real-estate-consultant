"""Account-related Supabase Auth I/O (service-role client) and password checks."""

from __future__ import annotations

from typing import Any

import httpx
from supabase import (
    AsyncClient,
    AuthApiError,
    AuthInvalidCredentialsError,
    AuthWeakPasswordError,
)
from supabase_auth.types import User

from app.repositories.exceptions import (
    raise_admin_auth_api_error,
    raise_could_not_load_profile,
    raise_current_password_incorrect,
    raise_password_auth_transport_unavailable,
    raise_password_verification_unavailable,
    raise_profile_service_unavailable,
    raise_weak_password,
)


async def verify_current_email_password(
    client: AsyncClient,
    *,
    email: str,
    password: str,
) -> None:
    try:
        await client.auth.sign_in_with_password({"email": email, "password": password})
    except AuthInvalidCredentialsError as exc:
        raise_current_password_incorrect(cause=exc)
    except AuthApiError as exc:
        if exc.code in ("invalid_credentials", "invalid_grant"):
            raise_current_password_incorrect(cause=exc)
        raise_password_verification_unavailable(cause=exc)
    except httpx.HTTPError as exc:
        raise_password_auth_transport_unavailable(cause=exc)


async def get_auth_user(client: AsyncClient, user_id: str) -> User:
    try:
        return (await client.auth.admin.get_user_by_id(user_id)).user

    except AuthApiError as exc:
        raise_could_not_load_profile(cause=exc)

    except httpx.HTTPError as exc:
        raise_could_not_load_profile(cause=exc)


async def update_auth_user(
    client: AsyncClient,
    user_id: str,
    attributes: dict[str, Any],
) -> None:
    try:
        await client.auth.admin.update_user_by_id(user_id, attributes)

    except AuthApiError as exc:
        raise_admin_auth_api_error(exc)

    except httpx.HTTPError as exc:
        raise_profile_service_unavailable(cause=exc)


async def update_auth_user_password(
    client: AsyncClient,
    user_id: str,
    *,
    new_password: str,
) -> None:
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
        raise_profile_service_unavailable(cause=exc)
