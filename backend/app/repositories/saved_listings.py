"""Per-user saved listings stored in ``public.saved_listings`` (Supabase)."""

from __future__ import annotations

from uuid import UUID

from supabase import AsyncClient

from app.core.db_safe import execute_db_safe
from app.utils.supabase.response import as_row_list


async def list_saved_property_ids(client: AsyncClient, user_id: UUID) -> list[str]:
    result = await execute_db_safe(
        client.table("saved_listings")
        .select("property_id")
        .eq("user_id", str(user_id))
        .order("created_at", desc=True)
        .execute(),
    )
    rows = as_row_list(result.data)
    return [
        row["property_id"]
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("property_id"), str)
    ]


async def add_saved_listing(
    client: AsyncClient,
    user_id: UUID,
    property_id: str,
) -> None:
    """Idempotent add (upsert on the (user_id, property_id) primary key)."""
    await execute_db_safe(
        client.table("saved_listings")
        .upsert({"user_id": str(user_id), "property_id": property_id})
        .execute(),
    )


async def remove_saved_listing(
    client: AsyncClient,
    user_id: UUID,
    property_id: str,
) -> None:
    await execute_db_safe(
        client.table("saved_listings")
        .delete()
        .eq("user_id", str(user_id))
        .eq("property_id", property_id)
        .execute(),
    )
