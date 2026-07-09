"""``public.jobs`` (Supabase) — ingestion job queue."""

from __future__ import annotations

from typing import Any

from supabase import AsyncClient

from app.core.db_safe import execute_db_safe
from app.utils.supabase.response import as_row_list, get_single_row

_ACTIVE_STATUSES = ("pending", "running")
_INSERT_ERROR = "Unexpected response from Supabase when creating ingestion job."


async def find_active_job_by_idempotency_key(
    client: AsyncClient,
    idempotency_key: str,
) -> dict[str, Any] | None:
    """Return the pending/running job for this key, if one is already queued."""
    result = await execute_db_safe(
        client.table("jobs")
        .select("id,status")
        .eq("idempotency_key", idempotency_key)
        .in_("status", _ACTIVE_STATUSES)
        .limit(1)
        .execute(),
    )
    rows = as_row_list(result.data)
    return rows[0] if rows else None


async def insert_job_row(
    client: AsyncClient,
    *,
    source: str,
    idempotency_key: str,
) -> dict[str, Any]:
    result = await execute_db_safe(
        client.table("jobs")
        .insert({"source": source, "idempotency_key": idempotency_key})
        .execute(),
    )
    return get_single_row(result, detail=_INSERT_ERROR)
