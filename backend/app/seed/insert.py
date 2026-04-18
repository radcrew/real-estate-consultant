"""Insert parsed `Properties` rows into Supabase `public.properties`."""

from __future__ import annotations

import logging

from supabase import AsyncClient

from app.models.properties import Properties
from app.seed.db_safe import execute_db_safe

logger = logging.getLogger(__name__)


async def insert_properties(client: AsyncClient, rows: list[Properties]) -> int:
    if not rows:
        logger.info("Supabase properties insert: no rows, skipping")
        return 0
    payload = [row.model_dump() for row in rows]
    logger.info("Supabase properties insert: inserting %d row(s)", len(payload))

    result = await execute_db_safe(
        client.table("properties").insert(payload).execute(),
    )

    if isinstance(result.data, list):
        n = len(result.data)
        logger.info("Supabase properties insert: PostgREST returned %d row(s)", n)
        return n

    logger.info(
        "Supabase properties insert: no row data in response, assuming %d sent",
        len(payload),
    )
    return len(payload)
