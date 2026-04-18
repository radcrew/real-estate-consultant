"""Insert parsed `Properties` rows into Supabase `public.properties` and related seed tables."""

from __future__ import annotations

import logging
from typing import Any

from supabase import AsyncClient

from app.models.properties import Properties
from app.seed.db_safe import execute_db_safe

logger = logging.getLogger(__name__)

_INSERT_CHUNK = 500


async def delete_property_images_for_property_ids(
    client: AsyncClient,
    property_ids: list[str],
) -> None:
    """Remove image rows for the given properties (avoids duplicates on re-seed)."""
    if not property_ids:
        return
    for start in range(0, len(property_ids), _INSERT_CHUNK):
        chunk = property_ids[start : start + _INSERT_CHUNK]
        await execute_db_safe(
            client.table("property_images").delete().in_("property_id", chunk).execute(),
        )
    logger.info(
        "Supabase property_images delete: cleared rows for %d property id(s)",
        len(property_ids),
    )


async def insert_properties(client: AsyncClient, rows: list[Properties]) -> int:
    if not rows:
        logger.info("Supabase properties upsert: no rows, skipping")
        return 0
    payload = [row.model_dump(mode="json", exclude_none=True) for row in rows]
    logger.info("Supabase properties upsert: upserting %d row(s) on conflict (id)", len(payload))

    result = await execute_db_safe(
        client.table("properties").upsert(payload, on_conflict="id").execute(),
    )

    if isinstance(result.data, list):
        n = len(result.data)
        logger.info("Supabase properties upsert: PostgREST returned %d row(s)", n)
        return n

    logger.info(
        "Supabase properties upsert: no row data in response, assuming %d sent",
        len(payload),
    )
    return len(payload)


async def insert_property_images(client: AsyncClient, rows: list[dict[str, Any]]) -> int:
    """Insert rows into ``public.property_images`` (``property_id``, ``url``)."""
    if not rows:
        logger.info("Supabase property_images insert: no rows, skipping")
        return 0
    total = 0
    for start in range(0, len(rows), _INSERT_CHUNK):
        chunk = rows[start : start + _INSERT_CHUNK]
        logger.info(
            "Supabase property_images insert: inserting chunk %d–%d of %d row(s)",
            start + 1,
            start + len(chunk),
            len(rows),
        )
        result = await execute_db_safe(
            client.table("property_images").insert(chunk).execute(),
        )
        if isinstance(result.data, list):
            total += len(result.data)
        else:
            total += len(chunk)
    logger.info("Supabase property_images insert: done (%d row(s))", total)
    return total
