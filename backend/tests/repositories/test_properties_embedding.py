"""Tests for the listing-embedding repository functions."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.db.property_row import EMBEDDING_DIMENSIONS
from app.repositories.properties import (
    list_property_ids_needing_embedding,
    list_similar_by_embedding,
    set_property_embedding,
)

_FIELDS = dict(
    address="100 Main St",
    city="Austin",
    state="TX",
    country="US",
    latitude=30.0,
    longitude=-97.0,
    property_type="Industrial",
    listing_type="PropertyForSale",
    description="A warehouse.",
    size_sqft=10000,
    price=1_000_000,
    rent=None,
    clear_height=24,
    loading_docks=2,
    listing_broker_name="Bob",
    listing_broker_email="bob@example.com",
    listing_broker_phone="555-0100",
)


def _vector(value: float = 0.1, *, width: int = EMBEDDING_DIMENSIONS) -> list[float]:
    return [value] * width


def _row(**overrides):
    return SimpleNamespace(id=uuid4(), **{**_FIELDS, **overrides})


def _session_returning(rows) -> MagicMock:
    session = MagicMock()
    result = MagicMock()
    result.all.return_value = rows
    result.scalars.return_value.all.return_value = rows
    session.execute = AsyncMock(return_value=result)
    return session


class TestRequireEmbeddingWidth:
    async def test_set_rejects_wrong_width(self):
        """A 384-dim vector from the HF model must not silently corrupt the column."""
        session = _session_returning([])
        with pytest.raises(HTTPException) as info:
            await set_property_embedding(
                session, property_id=uuid4(), embedding=_vector(width=384), model="minilm"
            )
        assert info.value.status_code == 502
        session.execute.assert_not_awaited()

    async def test_search_rejects_wrong_width(self):
        session = _session_returning([])
        with pytest.raises(HTTPException) as info:
            await list_similar_by_embedding(
                session, seed_id=uuid4(), embedding=_vector(width=384)
            )
        assert info.value.status_code == 502
        session.execute.assert_not_awaited()


class TestSetPropertyEmbedding:
    async def test_issues_update_with_model(self):
        session = _session_returning([])
        await set_property_embedding(
            session, property_id=uuid4(), embedding=_vector(), model="cohere.embed-english-v3"
        )
        session.execute.assert_awaited_once()
        compiled = str(session.execute.await_args.args[0])
        assert "UPDATE properties" in compiled
        assert "embedding_model" in compiled
        assert "embedded_at" in compiled


class TestListPropertyIdsNeedingEmbedding:
    async def test_zero_limit_short_circuits(self):
        session = _session_returning([])
        assert await list_property_ids_needing_embedding(session, model="m", limit=0) == []
        session.execute.assert_not_awaited()

    async def test_selects_null_or_superseded_model(self):
        ids = [uuid4(), uuid4()]
        session = _session_returning(ids)
        assert await list_property_ids_needing_embedding(session, model="m") == ids
        compiled = str(session.execute.await_args.args[0])
        assert "embedding IS NULL" in compiled
        assert "IS DISTINCT FROM" in compiled


class TestListSimilarByEmbedding:
    async def test_zero_limit_short_circuits(self):
        session = _session_returning([])
        result = await list_similar_by_embedding(
            session, seed_id=uuid4(), embedding=_vector(), limit=0
        )
        assert result == []
        session.execute.assert_not_awaited()

    async def test_converts_distance_to_similarity(self):
        """The service scores on similarity; pgvector returns cosine distance."""
        session = _session_returning([(_row(), 0.25), (_row(), 0.75)])
        result = await list_similar_by_embedding(session, seed_id=uuid4(), embedding=_vector())
        assert [round(score, 4) for _, score in result] == [0.75, 0.25]

    async def test_orders_by_distance_and_excludes_unembedded(self):
        session = _session_returning([])
        await list_similar_by_embedding(session, seed_id=uuid4(), embedding=_vector())
        compiled = str(session.execute.await_args.args[0])
        assert "ORDER BY distance ASC" in compiled
        assert "embedding IS NOT NULL" in compiled

    async def test_filters_are_optional(self):
        session = _session_returning([])
        await list_similar_by_embedding(session, seed_id=uuid4(), embedding=_vector())
        compiled = str(session.execute.await_args.args[0])
        assert "lower(coalesce(properties.state" not in compiled

    async def test_applies_supplied_filters(self):
        session = _session_returning([])
        await list_similar_by_embedding(
            session,
            seed_id=uuid4(),
            embedding=_vector(),
            state="TX",
            city="Austin",
            property_type="Industrial",
        )
        compiled = str(session.execute.await_args.args[0])
        for column in ("properties.state", "properties.city", "properties.property_type"):
            assert f"lower(coalesce({column}" in compiled

    async def test_blank_filter_is_ignored(self):
        session = _session_returning([])
        await list_similar_by_embedding(
            session, seed_id=uuid4(), embedding=_vector(), state="   "
        )
        compiled = str(session.execute.await_args.args[0])
        assert "lower(coalesce(properties.state" not in compiled

    async def test_returns_search_shaped_rows(self):
        session = _session_returning([(_row(city="Dallas"), 0.1)])
        result = await list_similar_by_embedding(session, seed_id=uuid4(), embedding=_vector())
        row, _ = result[0]
        assert row["city"] == "Dallas"
        assert "id" in row
