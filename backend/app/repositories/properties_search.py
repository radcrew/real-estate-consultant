"""Search ``public.properties`` with intake ``criteria`` + SQLAlchemy scoring."""

from __future__ import annotations

from typing import Any

from sqlalchemy import Float, and_, case, cast, func, literal, or_, select, true
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import AsyncClient
from app.core.db_safe import execute_db_safe
from app.utils.supabase_response import as_row_list

from app.db.property_row import PropertyRow


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _litf(x: float) -> Any:
    return cast(literal(x), Float)


def _ilike_pattern(term: str) -> str:
    esc = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{esc}%"


def _parse_range(bounds: Any) -> tuple[float | None, float | None]:
    if not isinstance(bounds, dict):
        return None, None
    return _float_or_none(bounds.get("min")), _float_or_none(bounds.get("max"))


def _target_sigma(lo: float | None, hi: float | None) -> tuple[float | None, float]:
    """Gaussian center and sigma (sigma >= 1), from intake ``min`` / ``max``."""
    if lo is not None and hi is not None:
        mid = (lo + hi) / 2.0
        span = abs(hi - lo)
        return mid, max(span / 2.0, 1.0)
    if lo is not None:
        return lo, max(abs(lo) * 0.15, 1.0)
    if hi is not None:
        return hi, max(abs(hi) * 0.15, 1.0)
    return None, 1.0


LocFields = tuple[str | None, str | None, str | None, str | None]


def _location_fields(criteria: dict[str, Any]) -> LocFields:
    """Parse ``(label, city, state, country)`` from ``criteria["location"]``."""
    loc = criteria.get("location")
    if isinstance(loc, str):
        t = loc.strip()
        return (t if t else None), None, None, None
    if isinstance(loc, dict):

        def _s(key: str) -> str | None:
            v = loc.get(key)
            return v.strip() if isinstance(v, str) and v.strip() else None

        lab = _s("label")
        return lab, _s("city"), _s("state"), _s("country")
    return None, None, None, None


def _lower_eq(col: Any, value: str) -> Any:
    return func.lower(func.coalesce(col, "")) == func.lower(literal(value))


def _location_score_expr(
    label: str | None,
    city: str | None,
    state: str | None,
    country: str | None,
) -> Any:
    """Tiered location: city 1.0, state 0.7, country 0.4; label uses ILIKE on each tier."""
    p = PropertyRow
    if city or state or country:
        parts: list[tuple[Any, Any]] = []
        if city:
            parts.append((_lower_eq(p.city, city), _litf(1.0)))
        if state:
            parts.append((_lower_eq(p.state, state), _litf(0.7)))
        if country:
            parts.append((_lower_eq(p.country, country), _litf(0.4)))
        if not parts:
            return _litf(1.0)
        return case(*parts, else_=_litf(0.0))
    if label:
        pat = _ilike_pattern(label)
        return case(
            (p.city.ilike(pat, escape="\\"), _litf(1.0)),
            (p.state.ilike(pat, escape="\\"), _litf(0.7)),
            (p.country.ilike(pat, escape="\\"), _litf(0.4)),
            else_=_litf(0.0),
        )
    return _litf(1.0)


def _gaussian(col: Any, target: float | None, sigma: float) -> Any:
    """Gaussian on ``col``; neutral 1.0 without target; 0 when ``col`` is null."""
    if target is None:
        return _litf(1.0)
    s = max(sigma, 1.0)
    denom = _litf(2.0 * s * s)
    c = cast(col, Float)
    t = _litf(target)
    inner = -func.pow(c - t, 2) / denom
    return case((col.is_(None), _litf(0.0)), else_=func.exp(inner))


def _where_property_type(raw: Any) -> Any:
    if isinstance(raw, str) and raw.strip():
        pat = _ilike_pattern(raw.strip())
        return PropertyRow.property_type.ilike(pat, escape="\\")
    if isinstance(raw, list):
        terms = [item.strip() for item in raw if isinstance(item, str) and item.strip()]
        if not terms:
            return true()
        pats = [PropertyRow.property_type.ilike(_ilike_pattern(t), escape="\\") for t in terms]
        return or_(*pats)
    return true()


def _where_location(
    label: str | None,
    city: str | None,
    state: str | None,
    country: str | None,
) -> Any:
    p = PropertyRow
    if city or state or country:
        clauses: list[Any] = []
        if country:
            clauses.append(_lower_eq(p.country, country))
        if state:
            clauses.append(_lower_eq(p.state, state))
        if city:
            clauses.append(_lower_eq(p.city, city))
        if clauses:
            return and_(*clauses)
    if label:
        pat = _ilike_pattern(label)
        return or_(
            p.city.ilike(pat, escape="\\"),
            p.state.ilike(pat, escape="\\"),
            func.coalesce(p.address, "").ilike(pat, escape="\\"),
            func.coalesce(p.country, "").ilike(pat, escape="\\"),
        )
    return true()


def _where_numeric(col: Any, bounds: Any) -> Any:
    if not isinstance(bounds, dict):
        return true()
    lo, hi = _parse_range(bounds)
    parts: list[Any] = []
    if lo is not None:
        parts.append(or_(col.is_(None), col >= lo))
    if hi is not None:
        parts.append(or_(col.is_(None), col <= hi))
    if not parts:
        return true()
    return and_(*parts)


def _where_criteria(criteria: dict[str, Any]) -> Any:
    c = criteria
    label, city, state, country = _location_fields(c)
    loc_clause = _where_location(label, city, state, country)
    return and_(
        _where_property_type(c.get("property_type")),
        loc_clause,
        _where_numeric(PropertyRow.price, c.get("price")),
        _where_numeric(PropertyRow.size_sqft, c.get("size_sqft")),
    )


def _score_expr(criteria: dict[str, Any]) -> Any:
    label, city, state, country = _location_fields(criteria)
    loc = _location_score_expr(label, city, state, country)

    p_lo, p_hi = _parse_range(criteria.get("price"))
    p_target, p_sigma = _target_sigma(p_lo, p_hi)
    price_s = _gaussian(PropertyRow.price, p_target, p_sigma)

    s_lo, s_hi = _parse_range(criteria.get("size_sqft"))
    s_target, s_sigma = _target_sigma(s_lo, s_hi)
    size_s = _gaussian(PropertyRow.size_sqft, s_target, s_sigma)

    raw = _litf(0.4) * loc + _litf(0.3) * price_s + _litf(0.3) * size_s
    return func.least(_litf(100.0), func.greatest(_litf(0.0), _litf(100.0) * raw))


def _row_to_property_dict(row: PropertyRow) -> dict[str, Any]:
    return {
        "id": row.id,
        "address": row.address,
        "city": row.city,
        "state": row.state,
        "country": row.country,
        "latitude": row.latitude,
        "longitude": row.longitude,
        "property_type": row.property_type,
        "listing_type": row.listing_type,
        "description": row.description,
        "size_sqft": row.size_sqft,
        "price": row.price,
        "rent": row.rent,
        "clear_height": row.clear_height,
        "loading_docks": row.loading_docks,
    }


async def search_properties(
    # session: AsyncSession,
    client: AsyncClient,
    criteria: Any,
    *,
    limit: int,
    offset: int,
) -> tuple[list[tuple[dict[str, Any], float]], int]:
    """Filter by intake criteria; rank by weighted location + Gaussian price + Gaussian size."""
    c = criteria if isinstance(criteria, dict) else {}
    lim = max(1, min(limit, 100))
    off = max(0, offset)
    """
    where_clause = _where_criteria(c)
    score = _score_expr(c).label("match_score")

    count_stmt = select(func.count()).select_from(PropertyRow).where(where_clause)
    total = int(await session.scalar(count_stmt) or 0)
    if total == 0:
        return [], 0

    stmt = (
        select(PropertyRow, score)
        .where(where_clause)
        .order_by(score.desc(), PropertyRow.id)
        .limit(lim)
        .offset(off)
    )
    result = await session.execute(stmt)
    out: list[tuple[dict[str, Any], float]] = []
    for prop, sc in result.all():
        out.append((_row_to_property_dict(prop), float(sc or 0.0)))
    return out, total
    """

     # No criteria: unfiltered list, same pagination as PostgREST range
    q = client.table("properties").select("*", count="exact")
    result = await execute_db_safe(
        q.order("id").range(off, off + lim - 1).execute(),
    )
    rows = as_row_list(result.data)
    total = int(result.count) if getattr(result, "count", None) is not None else len(rows)
    out: list[tuple[dict[str, Any], float]] = []
    for raw in rows:
        row = dict(raw)
        out.append((row, 100.0))
    return out, total
