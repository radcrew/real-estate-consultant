"""Search ``public.properties`` using explicit search criteria (from GET query params)."""

from __future__ import annotations

from typing import Any

from supabase import AsyncClient

from app.core.db_safe import execute_db_safe
from app.utils.supabase_response import as_row_list


def build_search_query(query: Any, criteria: dict[str, Any]) -> Any:
    """Apply ``type``, ``location``, price range, and size range to a ``properties`` query."""
    if t := criteria.get("type"):
        query = query.ilike("property_type", f"%{t}%")

    if loc := criteria.get("location"):
        query = query.or_(
            f"city.ilike.%{loc}%,state.ilike.%{loc}%,address.ilike.%{loc}%,country.ilike.%{loc}%"
        )

    if (v := criteria.get("minPrice")) is not None:
        query = query.gte("price", v)
    if (v := criteria.get("maxPrice")) is not None:
        query = query.lte("price", v)
    if (v := criteria.get("minSize")) is not None:
        query = query.gte("size_sqft", v)
    if (v := criteria.get("maxSize")) is not None:
        query = query.lte("size_sqft", v)

    return query


async def search_properties(
    client: AsyncClient,
    criteria: dict[str, Any],
    *,
    limit: int,
    offset: int,
) -> tuple[list[dict[str, Any]], int]:
    """Return property rows and total count for the current filters."""
    result = await execute_db_safe(
        build_search_query(
            client.table("properties").select("*", count="exact"),
            criteria,
        )
        .order("id")
        .range(offset, offset + max(limit, 1) - 1)
        .execute(),
    )
    rows = as_row_list(result.data)
    total = int(result.count) if getattr(result, "count", None) is not None else len(rows)
    return rows, total
