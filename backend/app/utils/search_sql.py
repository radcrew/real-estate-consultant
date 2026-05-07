"""SQLAlchemy expressions and row mapping for property search."""

from __future__ import annotations

from typing import Any

from sqlalchemy import Float, and_, case, cast, func, literal, or_, true

from app.db.property_row import PropertyRow
from app.utils.criteria_search import (
    gaussian_target_sigma,
    ilike_pattern,
    parse_location_fields,
    parse_range,
)


def _lit_float(x: float) -> Any:
    return cast(literal(x), Float)


def _lower_eq(col: Any, value: str) -> Any:
    return func.lower(func.coalesce(col, "")) == func.lower(literal(value))


def location_score_expr(
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
            parts.append((_lower_eq(p.city, city), _lit_float(1.0)))
        if state:
            parts.append((_lower_eq(p.state, state), _lit_float(0.7)))
        if country:
            parts.append((_lower_eq(p.country, country), _lit_float(0.4)))
        if not parts:
            return _lit_float(1.0)
        return case(*parts, else_=_lit_float(0.0))
    if label:
        pat = ilike_pattern(label)
        return case(
            (p.city.ilike(pat, escape="\\"), _lit_float(1.0)),
            (p.state.ilike(pat, escape="\\"), _lit_float(0.7)),
            (p.country.ilike(pat, escape="\\"), _lit_float(0.4)),
            else_=_lit_float(0.0),
        )
    return _lit_float(1.0)


def gaussian_score(col: Any, target: float | None, sigma: float) -> Any:
    """Gaussian on ``col``; neutral 1.0 without target; 0 when ``col`` is null."""
    if target is None:
        return _lit_float(1.0)
    s = max(sigma, 1.0)
    denom = _lit_float(2.0 * s * s)
    c = cast(col, Float)
    t = _lit_float(target)
    inner = -func.pow(c - t, 2) / denom
    return case((col.is_(None), _lit_float(0.0)), else_=func.exp(inner))


def where_property_type(raw: Any) -> Any:
    if isinstance(raw, str) and raw.strip():
        pat = ilike_pattern(raw.strip())
        return PropertyRow.property_type.ilike(pat, escape="\\")
    if isinstance(raw, list):
        terms = [item.strip() for item in raw if isinstance(item, str) and item.strip()]
        if not terms:
            return true()
        pats = [PropertyRow.property_type.ilike(ilike_pattern(t), escape="\\") for t in terms]
        return or_(*pats)
    return true()


def where_location(
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
        pat = ilike_pattern(label)
        return or_(
            p.city.ilike(pat, escape="\\"),
            p.state.ilike(pat, escape="\\"),
            func.coalesce(p.address, "").ilike(pat, escape="\\"),
            func.coalesce(p.country, "").ilike(pat, escape="\\"),
        )
    return true()


def where_numeric_bounds(col: Any, bounds: Any) -> Any:
    if not isinstance(bounds, dict):
        return true()
    lo, hi = parse_range(bounds)
    parts: list[Any] = []
    if lo is not None:
        parts.append(or_(col.is_(None), col >= lo))
    if hi is not None:
        parts.append(or_(col.is_(None), col <= hi))
    if not parts:
        return true()
    return and_(*parts)


def where_criteria(criteria: dict[str, Any]) -> Any:
    c = criteria
    label, city, state, country = parse_location_fields(c)
    loc_clause = where_location(label, city, state, country)
    return and_(
        where_property_type(c.get("property_type")),
        loc_clause,
        where_numeric_bounds(PropertyRow.price, c.get("price")),
        where_numeric_bounds(PropertyRow.size_sqft, c.get("size_sqft")),
    )


def match_score_expr(criteria: dict[str, Any]) -> Any:
    label, city, state, country = parse_location_fields(criteria)
    loc = location_score_expr(label, city, state, country)

    p_lo, p_hi = parse_range(criteria.get("price"))
    p_target, p_sigma = gaussian_target_sigma(p_lo, p_hi)
    price_s = gaussian_score(PropertyRow.price, p_target, p_sigma)

    s_lo, s_hi = parse_range(criteria.get("size_sqft"))
    s_target, s_sigma = gaussian_target_sigma(s_lo, s_hi)
    size_s = gaussian_score(PropertyRow.size_sqft, s_target, s_sigma)

    raw = _lit_float(0.4) * loc + _lit_float(0.3) * price_s + _lit_float(0.3) * size_s
    return func.least(_lit_float(100.0), func.greatest(_lit_float(0.0), _lit_float(100.0) * raw))


def property_row_to_search_dict(row: PropertyRow) -> dict[str, Any]:
    """ORM row to API/search payload keys (no ``image``; endpoint merges that)."""
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
