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
    if city or state or country:
        parts: list[tuple[Any, Any]] = []
        if city:
            parts.append((_lower_eq(PropertyRow.city, city), _lit_float(1.0)))
        if state:
            parts.append((_lower_eq(PropertyRow.state, state), _lit_float(0.7)))
        if country:
            parts.append((_lower_eq(PropertyRow.country, country), _lit_float(0.4)))
        if not parts:
            return _lit_float(1.0)
        return case(*parts, else_=_lit_float(0.0))

    if label:
        pattern = ilike_pattern(label)
        return case(
            (PropertyRow.city.ilike(pattern, escape="\\"), _lit_float(1.0)),
            (PropertyRow.state.ilike(pattern, escape="\\"), _lit_float(0.7)),
            (PropertyRow.country.ilike(pattern, escape="\\"), _lit_float(0.4)),
            else_=_lit_float(0.0),
        )

    return _lit_float(1.0)


def gaussian_score(column: Any, target: float | None, sigma: float) -> Any:
    """Gaussian on ``column``; neutral 1.0 without target; 0 when ``column`` is null."""
    if target is None:
        return _lit_float(1.0)
    effective_sigma = max(sigma, 1.0)
    denominator = _lit_float(2.0 * effective_sigma * effective_sigma)
    column_float = cast(column, Float)
    target_float = _lit_float(target)
    gaussian_exponent = -func.pow(column_float - target_float, 2) / denominator
    return case((column.is_(None), _lit_float(0.0)), else_=func.exp(gaussian_exponent))


def _gaussian_score_for_criterion(col: Any, bounds: Any) -> Any:
    lo, hi = parse_range(bounds)
    target, sigma = gaussian_target_sigma(lo, hi)
    return gaussian_score(col, target, sigma)


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
    label_clause: Any | None = None
    if label:
        pattern = ilike_pattern(label)
        label_clause = or_(
            PropertyRow.city.ilike(pattern, escape="\\"),
            PropertyRow.state.ilike(pattern, escape="\\"),
            func.coalesce(PropertyRow.address, "").ilike(pattern, escape="\\"),
            func.coalesce(PropertyRow.country, "").ilike(pattern, escape="\\"),
        )

    if city or state or country:
        clauses: list[Any] = []
        if country:
            clauses.append(_lower_eq(PropertyRow.country, country))
        if state:
            clauses.append(_lower_eq(PropertyRow.state, state))
        if city:
            clauses.append(_lower_eq(PropertyRow.city, city))
        if clauses:
            structured_clause = and_(*clauses)
            if label_clause is not None:
                return or_(structured_clause, label_clause)
            return structured_clause
    if label_clause is not None:
        return label_clause
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
    label, city, state, country = parse_location_fields(criteria)
    loc_clause = where_location(label, city, state, country)
    return and_(
        where_property_type(criteria.get("property_type")),
        loc_clause,
        where_numeric_bounds(PropertyRow.price, criteria.get("price")),
        where_numeric_bounds(PropertyRow.size_sqft, criteria.get("size_sqft")),
    )


def match_score_expr(criteria: dict[str, Any]) -> Any:
    loc = location_score_expr(*parse_location_fields(criteria))
    price = _gaussian_score_for_criterion(PropertyRow.price, criteria.get("price"))
    size = _gaussian_score_for_criterion(PropertyRow.size_sqft, criteria.get("size_sqft"))
    raw_score_expr = _lit_float(0.4) * loc + _lit_float(0.3) * price + _lit_float(0.3) * size
    return func.least(_lit_float(100.0), func.greatest(_lit_float(0.0), _lit_float(100.0) * raw_score_expr))


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
