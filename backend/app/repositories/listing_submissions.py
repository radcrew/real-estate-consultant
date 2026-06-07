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
