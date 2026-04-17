"""Upsert parsed `Properties` rows into Supabase `public.properties`."""

from __future__ import annotations

from typing import Any

from supabase import AsyncClient

from app.models.properties import Properties


def _rows_for_upsert(rows: list[Properties]) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for i, row in enumerate(rows):
        if not row.source_property_id:
            msg = f"Row at index {i} is missing source_property_id (LoopNet propertyId)"
            raise ValueError(msg)
        payload.append(row.model_dump())
    return payload


async def upsert_properties(client: AsyncClient, rows: list[Properties]) -> int:
    """Upsert all rows on ``source_property_id``. Returns number of rows sent."""
    if not rows:
        return 0
    payload = _rows_for_upsert(rows)
    result = await (
        client.table("properties").upsert(payload, on_conflict="source_property_id").execute()
    )
    if isinstance(result.data, list):
        return len(result.data)
    return len(payload)
