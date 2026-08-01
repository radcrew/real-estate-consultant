"""Search ``public.properties`` with intake ``criteria`` + SQLAlchemy scoring."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import case, func, literal, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.property_row import PropertyRow
from app.domain.search_sql import (
    component_score_exprs,
    match_score_expr,
    property_row_to_search_dict,
    where_criteria,
)
from app.repositories.questions import list_question_key_metadata
from app.schemas.search import CriteriaFieldItem
from supabase import AsyncClient


async def search_properties(
    session: AsyncSession,
    criteria: Any,
    *,
    limit: int,
    offset: int,
) -> tuple[list[tuple[dict[str, Any], float]], int]:
    """Filter by intake criteria; rank by weighted location + Gaussian price + Gaussian size."""

    where_expr = where_criteria(criteria)
    score_expr = match_score_expr(criteria).label("match_score")

    count_query = select(func.count()).select_from(PropertyRow).where(where_expr)
    total = int(await session.scalar(count_query) or 0)
    if total == 0:
        return [], 0

    search_query = (
        select(PropertyRow, score_expr)
        .where(where_expr)
        .order_by(score_expr.desc(), PropertyRow.id)
        .limit(limit)
        .offset(offset)
    )

    result = await session.execute(search_query)
    rows: list[tuple[dict[str, Any], float]] = []
    for property_row, score in result.all():
        rows.append((property_row_to_search_dict(property_row), float(score or 0.0)))

    return rows, total


async def list_properties_by_broker(
    session: AsyncSession,
    broker_name: str,
    *,
    limit: int = 60,
) -> list[dict[str, Any]]:
    """All listings whose ``listing_broker_name`` matches (case-insensitive)."""
    query = (
        select(PropertyRow)
        .where(func.lower(PropertyRow.listing_broker_name) == broker_name.strip().lower())
        .order_by(PropertyRow.id)
        .limit(limit)
    )
    result = await session.execute(query)
    return [property_row_to_search_dict(row) for row in result.scalars().all()]


async def get_property_by_id(session: AsyncSession, property_id: UUID) -> dict[str, Any] | None:
    query = select(PropertyRow).where(PropertyRow.id == property_id).limit(1)
    result = await session.execute(query)
    row = result.scalar_one_or_none()
    if row is None:
        return None
    return property_row_to_search_dict(row)


async def list_similar_candidate_rows(
    session: AsyncSession,
    *,
    seed_id: UUID,
    state: str | None,
    city: str | None,
    property_type: str | None,
    limit: int = 40,
) -> list[dict[str, Any]]:
    """Load a bounded candidate pool for embedding similarity ranking.

    Prefers same state / city / property_type as the seed listing, then fills with
    other rows. Excludes the seed id. Ranking by embedding cosine happens in Python.
    """
    if limit <= 0:
        return []

    state_key = state.strip().lower() if isinstance(state, str) and state.strip() else None
    city_key = city.strip().lower() if isinstance(city, str) and city.strip() else None
    type_key = (
        property_type.strip().lower()
        if isinstance(property_type, str) and property_type.strip()
        else None
    )

    preference = literal(0)
    if state_key:
        preference = preference + case(
            (func.lower(func.coalesce(PropertyRow.state, "")) == state_key, 4),
            else_=0,
        )
    if city_key:
        preference = preference + case(
            (func.lower(func.coalesce(PropertyRow.city, "")) == city_key, 2),
            else_=0,
        )
    if type_key:
        preference = preference + case(
            (func.lower(func.coalesce(PropertyRow.property_type, "")) == type_key, 1),
            else_=0,
        )

    query = (
        select(PropertyRow)
        .where(PropertyRow.id != seed_id)
        .order_by(preference.desc(), PropertyRow.id)
        .limit(limit)
    )
    result = await session.execute(query)
    return [property_row_to_search_dict(row) for row in result.scalars().all()]


async def get_property_match_breakdown(
    session: AsyncSession,
    property_id: UUID,
    criteria: dict[str, Any],
) -> tuple[dict[str, Any], tuple[float, float, float, float]] | None:
    """Property row plus its (location, price, size, total) match-score components."""
    location_expr, price_expr, size_expr = component_score_exprs(criteria)
    total_expr = match_score_expr(criteria)

    query = (
        select(
            PropertyRow,
            location_expr.label("location_score"),
            price_expr.label("price_score"),
            size_expr.label("size_score"),
            total_expr.label("match_score"),
        )
        .where(PropertyRow.id == property_id)
        .limit(1)
    )
    result = await session.execute(query)
    row = result.first()
    if row is None:
        return None

    property_row, location_score, price_score, size_score, match_score = row
    return (
        property_row_to_search_dict(property_row),
        (float(location_score), float(price_score), float(size_score), float(match_score)),
    )


async def normalize_criteria(
    client: AsyncClient,
    criteria: dict[str, Any],
) -> dict[str, CriteriaFieldItem]:
    """Merge session ``criteria`` with every configured question key (insertion order preserved)."""
    normalized: dict[str, CriteriaFieldItem] = {}

    types, titles, units = await list_question_key_metadata(client)

    for key in types:
        qtype = types[key]
        label = titles[key]
        unit = units.get(key)
        if key in criteria:
            normalized[key] = CriteriaFieldItem(
                type=qtype,
                label=label,
                unit=unit,
                data=criteria[key]
            )
        else:
            normalized[key] = CriteriaFieldItem(type=qtype, label=label, unit=unit, data=None)

    for key, value in criteria.items():
        if key not in normalized:
            normalized[key] = CriteriaFieldItem(type="unknown", label="", unit=None, data=value)

    return normalized
