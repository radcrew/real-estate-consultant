"""Tests for find_similar_listings orchestration."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.services.similar_listings import find_similar_listings


def _seed(seed_id, **overrides):
    return {
        "id": seed_id,
        "city": "Austin",
        "state": "TX",
        "property_type": "Warehouse",
        "description": "Dock-high warehouse near I-35",
        **overrides,
    }


def _row(row_id, **overrides):
    return {"id": row_id, "city": "Austin", "state": "TX", **overrides}


class TestFindSimilarListings:
    async def test_missing_seed_returns_none(self):
        db = AsyncMock()
        with patch(
            "app.services.similar_listings.get_property_by_id",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await find_similar_listings(db, uuid4(), limit=3)
        assert result is None

    async def test_zero_limit_skips_embedding(self):
        seed_id = uuid4()
        db = AsyncMock()
        with (
            patch(
                "app.services.similar_listings.get_property_by_id",
                new_callable=AsyncMock,
                return_value=_seed(seed_id),
            ),
            patch("app.services.similar_listings.embed", new_callable=AsyncMock) as mock_embed,
        ):
            result = await find_similar_listings(db, seed_id, limit=0)
        assert result == []
        mock_embed.assert_not_called()

    async def test_embeds_only_the_seed(self):
        """The point of ingest-time embeddings: one call, not one per candidate."""
        seed_id = uuid4()
        db = AsyncMock()
        with (
            patch(
                "app.services.similar_listings.get_property_by_id",
                new_callable=AsyncMock,
                return_value=_seed(seed_id),
            ),
            patch(
                "app.services.similar_listings.embed",
                new_callable=AsyncMock,
                return_value=[[0.1, 0.2]],
            ) as mock_embed,
            patch(
                "app.services.similar_listings.list_similar_by_embedding",
                new_callable=AsyncMock,
                return_value=[(_row(uuid4()), 0.9)],
            ),
        ):
            await find_similar_listings(db, seed_id, limit=6)
        mock_embed.assert_awaited_once()
        assert len(mock_embed.await_args.kwargs["texts"]) == 1

    async def test_scores_similarity_on_the_match_scale(self):
        seed_id = uuid4()
        near_id, far_id = uuid4(), uuid4()
        db = AsyncMock()
        with (
            patch(
                "app.services.similar_listings.get_property_by_id",
                new_callable=AsyncMock,
                return_value=_seed(seed_id),
            ),
            patch(
                "app.services.similar_listings.embed",
                new_callable=AsyncMock,
                return_value=[[1.0, 0.0]],
            ),
            patch(
                "app.services.similar_listings.list_similar_by_embedding",
                new_callable=AsyncMock,
                return_value=[(_row(near_id), 0.95), (_row(far_id), 0.40)],
            ),
        ):
            result = await find_similar_listings(db, seed_id, limit=2)

        assert result is not None
        assert [row["id"] for row, _ in result] == [near_id, far_id]
        assert [score for _, score in result] == [95.0, 40.0]

    async def test_scopes_to_the_seed_state(self):
        seed_id = uuid4()
        db = AsyncMock()
        with (
            patch(
                "app.services.similar_listings.get_property_by_id",
                new_callable=AsyncMock,
                return_value=_seed(seed_id),
            ),
            patch(
                "app.services.similar_listings.embed",
                new_callable=AsyncMock,
                return_value=[[0.1, 0.2]],
            ),
            patch(
                "app.services.similar_listings.list_similar_by_embedding",
                new_callable=AsyncMock,
                return_value=[(_row(uuid4()), 0.9)] * 3,
            ) as mock_knn,
        ):
            await find_similar_listings(db, seed_id, limit=3)
        assert mock_knn.await_count == 1
        assert mock_knn.await_args.kwargs["state"] == "TX"

    async def test_widens_when_the_state_is_sparse(self):
        """The old pool filled from other states rather than returning short."""
        seed_id = uuid4()
        in_state, out_of_state = uuid4(), uuid4()
        db = AsyncMock()
        with (
            patch(
                "app.services.similar_listings.get_property_by_id",
                new_callable=AsyncMock,
                return_value=_seed(seed_id),
            ),
            patch(
                "app.services.similar_listings.embed",
                new_callable=AsyncMock,
                return_value=[[0.1, 0.2]],
            ),
            patch(
                "app.services.similar_listings.list_similar_by_embedding",
                new_callable=AsyncMock,
                side_effect=[
                    [(_row(in_state), 0.9)],
                    [(_row(out_of_state, state="OH"), 0.5)],
                ],
            ) as mock_knn,
        ):
            result = await find_similar_listings(db, seed_id, limit=3)

        assert mock_knn.await_count == 2
        second = mock_knn.await_args_list[1].kwargs
        assert second.get("state") is None
        assert list(second["exclude_ids"]) == [in_state]
        assert second["limit"] == 2
        assert result is not None
        assert [row["id"] for row, _ in result] == [in_state, out_of_state]

    async def test_does_not_widen_when_full(self):
        seed_id = uuid4()
        db = AsyncMock()
        with (
            patch(
                "app.services.similar_listings.get_property_by_id",
                new_callable=AsyncMock,
                return_value=_seed(seed_id),
            ),
            patch(
                "app.services.similar_listings.embed",
                new_callable=AsyncMock,
                return_value=[[0.1, 0.2]],
            ),
            patch(
                "app.services.similar_listings.list_similar_by_embedding",
                new_callable=AsyncMock,
                return_value=[(_row(uuid4()), 0.9), (_row(uuid4()), 0.8)],
            ) as mock_knn,
        ):
            await find_similar_listings(db, seed_id, limit=2)
        assert mock_knn.await_count == 1

    async def test_seed_without_state_queries_once(self):
        seed_id = uuid4()
        db = AsyncMock()
        with (
            patch(
                "app.services.similar_listings.get_property_by_id",
                new_callable=AsyncMock,
                return_value=_seed(seed_id, state=None),
            ),
            patch(
                "app.services.similar_listings.embed",
                new_callable=AsyncMock,
                return_value=[[0.1, 0.2]],
            ),
            patch(
                "app.services.similar_listings.list_similar_by_embedding",
                new_callable=AsyncMock,
                return_value=[],
            ) as mock_knn,
        ):
            result = await find_similar_listings(db, seed_id, limit=3)
        assert result == []
        assert mock_knn.await_count == 1

    async def test_empty_embedding_response_returns_empty(self):
        seed_id = uuid4()
        db = AsyncMock()
        with (
            patch(
                "app.services.similar_listings.get_property_by_id",
                new_callable=AsyncMock,
                return_value=_seed(seed_id),
            ),
            patch(
                "app.services.similar_listings.embed",
                new_callable=AsyncMock,
                return_value=[],
            ),
            patch(
                "app.services.similar_listings.list_similar_by_embedding",
                new_callable=AsyncMock,
            ) as mock_knn,
        ):
            result = await find_similar_listings(db, seed_id, limit=3)
        assert result == []
        mock_knn.assert_not_called()

    async def test_embeddings_unavailable_propagates(self):
        seed_id = uuid4()
        db = AsyncMock()
        with (
            patch(
                "app.services.similar_listings.get_property_by_id",
                new_callable=AsyncMock,
                return_value=_seed(seed_id),
            ),
            patch(
                "app.services.similar_listings.embed",
                new_callable=AsyncMock,
                side_effect=HTTPException(status_code=503, detail="Embeddings unavailable"),
            ),
        ):
            with pytest.raises(HTTPException) as info:
                await find_similar_listings(db, seed_id, limit=3)
        assert info.value.status_code == 503
        assert info.value.detail == "Embeddings unavailable"
