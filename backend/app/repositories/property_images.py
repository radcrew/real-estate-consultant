"""Supabase access to ``public.property_images`` for API enrichment."""

from __future__ import annotations

from uuid import UUID

from supabase import AsyncClient

from app.core.db_safe import execute_db_safe
from app.utils.supabase_response import as_row_list


async def fetch_first_image_url(
    client: AsyncClient,
    property_id: UUID,
) -> str | None:
    """First image ``url`` for this listing (smallest URL string when multiple rows exist)."""
    result = await execute_db_safe(
        client.table("property_images")
        .select("url")
        .eq("property_id", str(property_id))
        .order("url")
        .limit(1)
        .execute(),
    )
    rows = as_row_list(result.data)
    if not rows:
        return None
    raw_url = rows[0].get("url")
    if not isinstance(raw_url, str) or not raw_url.strip():
        return None
    return raw_url.strip()


async def fetch_all_image_urls(
    client: AsyncClient,
    property_id: UUID,
) -> list[str]:
    """All image ``url`` values for this listing (stable ascending ``url`` order)."""
    result = await execute_db_safe(
        client.table("property_images")
        .select("url")
        .eq("property_id", str(property_id))
        .order("url")
        .execute(),
    )
    rows = as_row_list(result.data)
    out: list[str] = []
    for row in rows:
        raw_url = row.get("url")
        if isinstance(raw_url, str) and raw_url.strip():
            out.append(raw_url.strip())
    return out
