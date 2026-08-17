"""Search ``public.properties`` with intake ``criteria`` + SQLAlchemy scoring."""

from __future__ import annotations

from collections.abc import Collection
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.property_row import EMBEDDING_DIMENSIONS, PropertyRow
from app.domain.search_sql import (
    component_score_exprs,
    match_score_expr,
    property_row_to_search_dict,
    where_criteria,
)
from app.repositories.questions import list_question_key_metadata
from app.schemas.search import CriteriaFieldItem
from app.utils.exceptions import raise_bad_gateway
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


def _require_embedding_width(embedding: list[float]) -> None:
    """Reject a wrong-width vector loudly.

    The column is fixed at ``EMBEDDING_DIMENSIONS`` and every stored vector must come
    from the same model, so a mismatch means the embeddings route is pointed at a model
    this schema cannot hold — not something to coerce or silently skip.
    """
    if len(embedding) != EMBEDDING_DIMENSIONS:
        raise_bad_gateway(
            "The embedding model does not match the configured vector size.",
        )


async def set_property_embedding(
    session: AsyncSession,
    *,
    property_id: UUID,
    embedding: list[float],
    model: str,
) -> None:
    """Store a listing's embedding, recording which model produced it."""
    _require_embedding_width(embedding)
    await session.execute(
        update(PropertyRow)
        .where(PropertyRow.id == property_id)
        .values(
            embedding=embedding,
            embedding_model=model,
            embedded_at=func.now(),
        )
    )


async def get_property_embedding(
    session: AsyncSession,
    property_id: UUID,
    *,
    model: str,
) -> list[float] | None:
    """Return a listing's stored vector, if it came from ``model``.

    The backfill embeds ``format_listing_block_for_fit(row)`` — the same text a query
    would re-embed — so for a seed that is itself an ingested listing the stored vector is
    not an approximation of the fresh one, it is the same vector. Reading it back turns
    similar-listings into a database-only request.

    ``None`` when the row has no vector yet or carries one from a superseded model:
    vectors from different models are not comparable, so the caller has to embed rather
    than mix them.
    """
    query = (
        select(PropertyRow.embedding)
        .where(
            PropertyRow.id == property_id,
            PropertyRow.embedding.is_not(None),
            PropertyRow.embedding_model == model,
        )
        .limit(1)
    )
    result = await session.execute(query)
    stored = result.scalar_one_or_none()
    return list(stored) if stored is not None else None


async def list_properties_needing_embedding(
    session: AsyncSession,
    *,
    model: str,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Rows with no embedding, or one produced by a superseded model.

    Returns full rows rather than ids because the caller has to rebuild the listing
    text to embed it; fetching ids first would only add a round trip per batch.
    """
    if limit <= 0:
        return []
    query = (
        select(PropertyRow)
        .where(
            or_(
                PropertyRow.embedding.is_(None),
                PropertyRow.embedding_model.is_distinct_from(model),
            )
        )
        .order_by(PropertyRow.id)
        .limit(limit)
    )
    result = await session.execute(query)
    return [property_row_to_search_dict(row) for row in result.scalars().all()]


async def list_similar_by_embedding(
    session: AsyncSession,
    *,
    seed_id: UUID,
    embedding: list[float],
    state: str | None = None,
    city: str | None = None,
    property_type: str | None = None,
    exclude_ids: Collection[UUID] | None = None,
    limit: int = 6,
) -> list[tuple[dict[str, Any], float]]:
    """Nearest neighbours by cosine distance, as ``(row, similarity 0–1)``.

    Any filter left as ``None`` is not applied, so the caller decides how tightly to
    scope locality. ``exclude_ids`` lets a caller widen its filters and top up without
    repeating rows it already has. Rows without an embedding are excluded — they would
    otherwise sort arbitrarily rather than being absent.
    """
    if limit <= 0:
        return []
    _require_embedding_width(embedding)

    distance = PropertyRow.embedding.cosine_distance(embedding).label("distance")
    conditions = [
        PropertyRow.id != seed_id,
        PropertyRow.embedding.is_not(None),
    ]
    if exclude_ids:
        conditions.append(PropertyRow.id.not_in(list(exclude_ids)))
    for column, value in (
        (PropertyRow.state, state),
        (PropertyRow.city, city),
        (PropertyRow.property_type, property_type),
    ):
        if isinstance(value, str) and value.strip():
            conditions.append(func.lower(func.coalesce(column, "")) == value.strip().lower())

    query = (
        select(PropertyRow, distance)
        .where(*conditions)
        .order_by(distance.asc(), PropertyRow.id)
        .limit(limit)
    )
    result = await session.execute(query)
    return [
        # Cosine distance is 1 - cosine similarity; the caller scores on similarity.
        (property_row_to_search_dict(row), 1.0 - float(value or 0.0))
        for row, value in result.all()
    ]


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
