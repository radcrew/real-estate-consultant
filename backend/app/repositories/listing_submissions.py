"""Persist public 'list your property' submissions to ``public.listing_submissions``."""

from __future__ import annotations

from typing import Any

from supabase import AsyncClient

from app.core.db_safe import execute_db_safe
from app.utils.exceptions import raise_bad_gateway
from app.utils.supabase.response import as_row_list

_INSERT_ERROR = "Unexpected response from Supabase when saving the submission."


async def create_listing_submission(
    client: AsyncClient,
    data: dict[str, Any],
) -> dict[str, Any]:
    result = await execute_db_safe(
        client.table("listing_submissions").insert(data).execute(),
    )
    rows = as_row_list(result.data)
    if not rows or not isinstance(rows[0], dict):
        raise_bad_gateway(_INSERT_ERROR)
    return rows[0]


async def list_listing_submissions(
    client: AsyncClient,
    *,
    status: str | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    query = (
        client.table("listing_submissions")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
    )
    if status:
        query = query.eq("status", status)
    result = await execute_db_safe(query.execute())
    return [row for row in as_row_list(result.data) if isinstance(row, dict)]


async def update_submission_status(
    client: AsyncClient,
    submission_id: str,
    status: str,
) -> dict[str, Any] | None:
    result = await execute_db_safe(
        client.table("listing_submissions")
        .update({"status": status})
        .eq("id", submission_id)
        .execute(),
    )
    rows = as_row_list(result.data)
    return rows[0] if rows and isinstance(rows[0], dict) else None
