"""``public.outreach_drafts`` (PostgREST via Supabase async client)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from supabase import AsyncClient

from app.core.db_safe import execute_db_safe
from app.utils.exceptions import raise_bad_gateway
from app.utils.supabase.response import as_row_list, get_single_row

_SELECT = "id,property_id,user_id,draft_email,created_at"
_UNEXPECTED = "Unexpected response from Supabase when loading outreach draft."


async def insert_outreach_draft(
    client: AsyncClient,
    *,
    user_id: UUID,
    property_id: UUID,
    draft_email: str,
) -> dict[str, Any]:
    result = await execute_db_safe(
        client.table("outreach_drafts")
        .insert(
            {
                "user_id": str(user_id),
                "property_id": str(property_id),
                "draft_email": draft_email,
            },
        )
        .select(_SELECT)
        .single()
        .execute(),
    )
    return get_single_row(result, detail=_UNEXPECTED)


async def fetch_outreach_draft_for_user(
    client: AsyncClient,
    *,
    draft_id: UUID,
    user_id: UUID,
) -> dict[str, Any] | None:
    result = await execute_db_safe(
        client.table("outreach_drafts")
        .select(_SELECT)
        .eq("id", str(draft_id))
        .eq("user_id", str(user_id))
        .limit(1)
        .execute(),
    )
    rows = as_row_list(result.data)
    if not rows:
        return None
    row = rows[0]
    if not isinstance(row, dict):
        raise_bad_gateway(_UNEXPECTED)
    return row


async def fetch_latest_outreach_draft_for_property(
    client: AsyncClient,
    *,
    user_id: UUID,
    property_id: UUID,
) -> dict[str, Any] | None:
    result = await execute_db_safe(
        client.table("outreach_drafts")
        .select(_SELECT)
        .eq("user_id", str(user_id))
        .eq("property_id", str(property_id))
        .order("created_at", desc=True)
        .limit(1)
        .execute(),
    )
    rows = as_row_list(result.data)
    if not rows:
        return None
    row = rows[0]
    if not isinstance(row, dict):
        raise_bad_gateway(_UNEXPECTED)
    return row


async def update_outreach_draft_email(
    client: AsyncClient,
    *,
    draft_id: UUID,
    user_id: UUID,
    draft_email: str,
) -> dict[str, Any] | None:
    result = await execute_db_safe(
        client.table("outreach_drafts")
        .update({"draft_email": draft_email})
        .eq("id", str(draft_id))
        .eq("user_id", str(user_id))
        .select(_SELECT)
        .limit(1)
        .execute(),
    )
    rows = as_row_list(result.data)
    if not rows:
        return None
    row = rows[0]
    if not isinstance(row, dict):
        raise_bad_gateway(_UNEXPECTED)
    return row
