"""Account-related Supabase Auth I/O (service-role client)."""

from __future__ import annotations

from typing import Any

import httpx

from app.models.auth_user import AuthUser, auth_user_from_supabase
from app.repositories.exceptions import (
    raise_admin_auth_api_error,
    raise_could_not_load_profile,
    raise_profile_service_unavailable,
)
from supabase import (
    AsyncClient,
    AuthApiError,
)


async def get_auth_user(client: AsyncClient, user_id: str) -> AuthUser:
    try:
        return auth_user_from_supabase((await client.auth.admin.get_user_by_id(user_id)).user)

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
