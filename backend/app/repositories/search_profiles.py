"""Persistence for ``public.search_profiles`` (Supabase)."""

from __future__ import annotations

from uuid import UUID

from supabase import AsyncClient

from app.core.db_safe import execute_db_safe
from app.exceptions.common import raise_bad_gateway
from app.exceptions.intake import raise_intake_session_not_found
from app.utils.supabase.response import as_row_list, get_single_row

_CREATE_PROFILE_ERROR = "Unexpected response from Supabase when creating search profile."


async def ensure_search_profile_access(
    client: AsyncClient,
    search_profile_id: object,
    user_id: UUID,
) -> str | None:
    if search_profile_id is None:
        return None

    owned_profile = await execute_db_safe(
        client.table("search_profiles")
        .select("id")
        .eq("id", str(search_profile_id))
        .eq("user_id", str(user_id))
        .limit(1)
        .execute(),
    )
    if not as_row_list(owned_profile.data):
        raise_intake_session_not_found()
    return str(search_profile_id)


async def create_search_profile(client: AsyncClient, user_id: UUID) -> str:
    result = await execute_db_safe(
        client.table("search_profiles").insert({"user_id": str(user_id)}).execute(),
    )
    row = get_single_row(result, detail=_CREATE_PROFILE_ERROR)
    profile_id = row.get("id")
    if not isinstance(profile_id, str):
        raise_bad_gateway(_CREATE_PROFILE_ERROR)
    return profile_id
