"""Insert parsed `Properties` rows into Supabase `public.properties`."""

from __future__ import annotations

import logging
from typing import Any

from supabase import AsyncClient

from app.models.properties import Properties

logger = logging.getLogger(__name__)


def _rows_for_insert(rows: list[Properties]) -> list[dict[str, Any]]:
    return [row.model_dump() for row in rows]


async def insert_properties(client: AsyncClient, rows: list[Properties]) -> int:
    """Insert all rows (no natural-key upsert). Re-seeding appends unless you truncate the table."""
    if not rows:
        logger.info("Supabase properties insert: no rows, skipping")
        return 0
    payload = _rows_for_insert(rows)
    logger.info("Supabase properties insert: inserting %d row(s)", len(payload))
    result = await client.table("properties").insert(payload).execute()
    if isinstance(result.data, list):
        n = len(result.data)
        logger.info("Supabase properties insert: PostgREST returned %d row(s)", n)
        return n
    logger.info(
        "Supabase properties insert: no row data in response, assuming %d sent",
        len(payload),
    )
    return len(payload)
