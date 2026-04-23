"""Supabase access for ``search_profiles`` used by intake completion."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from supabase import AsyncClient

from app.core.db_safe import execute_db_safe
from app.utils.intake_rows import intake_session_not_found
from app.utils.supabase_response import as_row_list, expect_single_row_from_result

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
        raise intake_session_not_found()
    return str(search_profile_id)


async def create_search_profile(client: AsyncClient, user_id: UUID) -> str:
    result = await execute_db_safe(
        client.table("search_profiles").insert({"user_id": str(user_id)}).execute(),
    )
    row = expect_single_row_from_result(result, detail=_CREATE_PROFILE_ERROR)
    profile_id = row.get("id")
    if not isinstance(profile_id, str):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=_CREATE_PROFILE_ERROR,
        )
    return profile_id
