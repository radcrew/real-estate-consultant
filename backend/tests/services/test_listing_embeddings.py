"""Tests for the listing-embedding backfill."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.services.listing_embeddings import backfill_listing_embeddings

_MODEL = "bedrock:cohere.embed-english-v3"


def _rows(count: int) -> list[dict]:
    return [{"id": uuid4(), "city": "Austin", "description": f"Listing {i}"} for i in range(count)]


def _patches(*, batches, vectors_for=lambda rows: [[0.1]] * len(rows)):
    """Patch the service's collaborators; ``batches`` is the sequence of row batches."""
    return (
        patch(
            "app.services.listing_embeddings.resolve_embeddings_model_id",
            return_value=_MODEL,
        ),
        patch(
            "app.services.listing_embeddings.list_properties_needing_embedding",
            new_callable=AsyncMock,
            side_effect=list(batches),
        ),
        patch(
            "app.services.listing_embeddings.embed",
            new_callable=AsyncMock,
            side_effect=lambda *, texts: vectors_for(texts),
        ),
        patch(
            "app.services.listing_embeddings.set_property_embedding",
            new_callable=AsyncMock,
        ),
    )


class TestBackfillListingEmbeddings:
    async def test_no_pending_rows_writes_nothing(self):
        session = AsyncMock()
        with (
            patch(
                "app.services.listing_embeddings.resolve_embeddings_model_id",
                return_value=_MODEL,
            ),
            patch(
                "app.services.listing_embeddings.list_properties_needing_embedding",
                new_callable=AsyncMock,
                return_value=[],
            ),
            patch("app.services.listing_embeddings.embed", new_callable=AsyncMock) as embed_,
            patch(
                "app.services.listing_embeddings.set_property_embedding",
                new_callable=AsyncMock,
            ) as setter,
        ):
            written = await backfill_listing_embeddings(session)
        assert written == 0
        embed_.assert_not_called()
        setter.assert_not_called()
        session.commit.assert_not_called()

    async def test_drains_until_empty(self):
        session = AsyncMock()
        first, second = _rows(3), _rows(2)
        model_p, find_p, embed_p, set_p = _patches(batches=[first, second, []])
        with model_p, find_p, embed_p, set_p as setter:
            written = await backfill_listing_embeddings(session, batch_size=3)
        assert written == 5
        assert setter.await_count == 5
        assert session.commit.await_count == 2

    async def test_commits_each_batch_so_a_run_can_resume(self):
        session = AsyncMock()
        model_p, find_p, embed_p, set_p = _patches(batches=[_rows(2), []])
        with model_p, find_p, embed_p, set_p:
            await backfill_listing_embeddings(session, batch_size=2)
        session.commit.assert_awaited_once()

    async def test_max_batches_bounds_the_run(self):
        session = AsyncMock()
        model_p, find_p, embed_p, set_p = _patches(batches=[_rows(2), _rows(2), _rows(2), []])
        with model_p, find_p, embed_p, set_p:
            written = await backfill_listing_embeddings(session, batch_size=2, max_batches=2)
        assert written == 4
        assert session.commit.await_count == 2

    async def test_records_the_active_model_with_each_vector(self):
        session = AsyncMock()
        model_p, find_p, embed_p, set_p = _patches(batches=[_rows(1), []])
        with model_p, find_p, embed_p, set_p as setter:
            await backfill_listing_embeddings(session)
        assert setter.await_args.kwargs["model"] == _MODEL

    async def test_vector_count_mismatch_raises_before_writing(self):
        """A positional zip would otherwise attach vectors to the wrong listings."""
        session = AsyncMock()
        model_p, find_p, embed_p, set_p = _patches(
            batches=[_rows(3), []],
            vectors_for=lambda texts: [[0.1]] * (len(texts) - 1),
        )
        with model_p, find_p, embed_p, set_p as setter:
            with pytest.raises(HTTPException) as info:
                await backfill_listing_embeddings(session)
        assert info.value.status_code == 502
        setter.assert_not_called()
        session.commit.assert_not_called()

    async def test_embeddings_error_propagates(self):
        session = AsyncMock()
        with (
            patch(
                "app.services.listing_embeddings.resolve_embeddings_model_id",
                return_value=_MODEL,
            ),
            patch(
                "app.services.listing_embeddings.list_properties_needing_embedding",
                new_callable=AsyncMock,
                return_value=_rows(2),
            ),
            patch(
                "app.services.listing_embeddings.embed",
                new_callable=AsyncMock,
                side_effect=HTTPException(status_code=503, detail="Embeddings unavailable"),
            ),
            patch(
                "app.services.listing_embeddings.set_property_embedding",
                new_callable=AsyncMock,
            ),
        ):
            with pytest.raises(HTTPException) as info:
                await backfill_listing_embeddings(session)
        assert info.value.status_code == 503
