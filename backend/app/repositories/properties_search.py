"""Search ``public.properties`` using explicit search criteria (from GET query params)."""

from __future__ import annotations

import re
from typing import Any

from supabase import AsyncClient

from app.core.db_safe import execute_db_safe
from app.utils.supabase_response import as_row_list


def _sanitize_ilike_literal(value: str) -> str:
    """Strip SQL LIKE wildcards so user input cannot broaden matches."""
    return re.sub(r"[%_]+", " ", value).strip()


def apply_criteria_to_properties_query(query: Any, criteria: dict[str, Any]) -> Any:
    """Apply ``type``, ``location``, price range, and size range to a ``properties`` query."""
    raw_type = criteria.get("type")
    if isinstance(raw_type, str) and raw_type.strip():
        esc = _sanitize_ilike_literal(raw_type.strip())
        if esc:
            query = query.ilike("property_type", f"%{esc}%")

    raw_location = criteria.get("location")
    if isinstance(raw_location, str) and raw_location.strip():
        esc = _sanitize_ilike_literal(raw_location.strip())
        if esc:
            query = query.or_(
                f"city.ilike.%{esc}%,state.ilike.%{esc}%,address.ilike.%{esc}%,country.ilike.%{esc}%"
            )

    min_price = criteria.get("minPrice")
    if min_price is not None:
        try:
            query = query.gte("price", float(min_price))
        except (TypeError, ValueError):
            pass

    max_price = criteria.get("maxPrice")
    if max_price is not None:
        try:
            query = query.lte("price", float(max_price))
        except (TypeError, ValueError):
            pass

    min_size = criteria.get("minSize")
    if min_size is not None:
        try:
            query = query.gte("size_sqft", float(min_size))
        except (TypeError, ValueError):
            pass

    max_size = criteria.get("maxSize")
    if max_size is not None:
        try:
            query = query.lte("size_sqft", float(max_size))
        except (TypeError, ValueError):
            pass

    return query


async def search_properties(
    client: AsyncClient,
    criteria: dict[str, Any],
    *,
    limit: int,
    offset: int,
) -> tuple[list[dict[str, Any]], int]:
    """Return property rows and total count for the current filters."""
    base = client.table("properties").select("*", count="exact")
    filtered = apply_criteria_to_properties_query(base, criteria)
    end = offset + max(limit, 1) - 1
    result = await execute_db_safe(filtered.order("id").range(offset, end).execute())
    rows = as_row_list(result.data)
    total = int(result.count) if getattr(result, "count", None) is not None else len(rows)
    return rows, total
