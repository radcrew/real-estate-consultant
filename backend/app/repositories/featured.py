"""Deterministic daily-rotating featured listings."""

from __future__ import annotations

import datetime
import random
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.property_row import PropertyRow
from app.utils.search_sql import property_row_to_search_dict

_FEATURED_COUNT = 6
_POOL_SIZE = 60


async def list_featured_property_rows(
    session: AsyncSession,
) -> list[dict[str, Any]]:
    """Return _FEATURED_COUNT listings, stable within a UTC day, rotating daily."""
    query = select(PropertyRow).order_by(PropertyRow.id).limit(_POOL_SIZE)
    result = await session.execute(query)
    rows = [property_row_to_search_dict(r) for r in result.scalars().all()]

    if not rows:
        return []

    today = datetime.datetime.now(datetime.UTC).date().isoformat()
    random.Random(today).shuffle(rows)
    return rows[:_FEATURED_COUNT]
