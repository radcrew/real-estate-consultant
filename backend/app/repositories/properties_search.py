"""Search ``public.properties`` using intake-style ``criteria`` (JSON from sessions)."""

from __future__ import annotations

from typing import Any

from supabase import AsyncClient

from app.core.db_safe import execute_db_safe
from app.utils.supabase_response import as_row_list


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _apply_numeric_range(query: Any, column: str, bounds: Any) -> Any:
    """Apply ``gte`` / ``lte`` from ``{"min": ..., "max": ...}`` when present."""
    if not isinstance(bounds, dict):
        return query
    lo = _float_or_none(bounds.get("min"))
    hi = _float_or_none(bounds.get("max"))
    if lo is not None:
        query = query.gte(column, lo)
    if hi is not None:
        query = query.lte(column, hi)
    return query


def _apply_location_string(query: Any, loc: str) -> Any:
    text = loc.strip()
    if not text:
        return query
    return query.or_(
        f"city.ilike.%{text}%,state.ilike.%{text}%,address.ilike.%{text}%,country.ilike.%{text}%"
    )


def _apply_property_type(query: Any, raw: Any) -> Any:
    """``property_type`` as a string or list of strings (OR of case-insensitive partial matches)."""
    if isinstance(raw, str) and raw.strip():
        return query.ilike("property_type", f"%{raw.strip()}%")
    if isinstance(raw, list):
        terms = [item.strip() for item in raw if isinstance(item, str) and item.strip()]
        if not terms:
            return query
        if len(terms) == 1:
            return query.ilike("property_type", f"%{terms[0]}%")
        clause = ",".join(f"property_type.ilike.%{t}%" for t in terms)
        return query.or_(clause)
    return query


def build_search_query(query: Any, criteria: dict[str, Any]) -> Any:
    """Apply intake-style criteria: ``price``, ``location``, ``size_sqft``, ``property_type``."""
    if not criteria:
        return query

    query = _apply_property_type(query, criteria.get("property_type"))

    loc = criteria.get("location")
    if isinstance(loc, str):
        query = _apply_location_string(query, loc)

    query = _apply_numeric_range(query, "price", criteria.get("price"))
    query = _apply_numeric_range(query, "size_sqft", criteria.get("size_sqft"))

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
