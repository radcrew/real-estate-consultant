"""``public.jobs`` (Supabase) — ingestion job queue."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from supabase import AsyncClient

from app.core.db_safe import execute_db_safe


async def claim_next_job(client: AsyncClient) -> dict[str, Any] | None:
    """Atomically claim the oldest pending job, if any."""
    result = await execute_db_safe(client.rpc("claim_next_job").execute())
    return result.data[0] if result.data else None


async def insert_job_row(client: AsyncClient, source: str) -> dict[str, Any]:
    result = await execute_db_safe(client.table("jobs").insert({"source": source}).execute())
    if not result.data:
        raise HTTPException(status_code=502, detail="Failed to enqueue job.")
    return result.data[0]


async def update_job_status(
    client: AsyncClient,
    job_id: str,
    status: str,
    *,
    result: dict[str, Any] | None = None,
    error: str | None = None,
) -> None:
    payload: dict[str, Any] = {"status": status}
    if result is not None:
        payload["result"] = result
    if error is not None:
        payload["error"] = error
    await execute_db_safe(client.table("jobs").update(payload).eq("id", job_id).execute())
