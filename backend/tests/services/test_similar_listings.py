"""Tests for find_similar_listings orchestration."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.services.similar_listings import find_similar_listings


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

    async def test_no_candidates_returns_empty(self):
        seed_id = uuid4()
        seed = {
            "id": seed_id,
            "city": "Austin",
            "state": "TX",
            "property_type": "Warehouse",
            "description": "Dock-high warehouse",
        }
        db = AsyncMock()
        with (
            patch(
                "app.services.similar_listings.get_property_by_id",
                new_callable=AsyncMock,
                return_value=seed,
            ),
            patch(
                "app.services.similar_listings.list_similar_candidate_rows",
                new_callable=AsyncMock,
                return_value=[],
            ),
            patch(
                "app.services.similar_listings.embed",
                new_callable=AsyncMock,
            ) as mock_embed,
        ):
            result = await find_similar_listings(db, seed_id, limit=3)
        assert result == []
        mock_embed.assert_not_called()

    async def test_ranks_by_cosine_similarity(self):
        seed_id = uuid4()
        near_id = uuid4()
        far_id = uuid4()
        seed = {
            "id": seed_id,
            "city": "Austin",
            "state": "TX",
            "property_type": "Warehouse",
            "description": "Dock-high warehouse near I-35",
        }
        near = {
            "id": near_id,
            "city": "Austin",
            "state": "TX",
            "property_type": "Warehouse",
            "description": "Warehouse with docks",
        }
        far = {
            "id": far_id,
            "city": "Dallas",
            "state": "TX",
            "property_type": "Office",
            "description": "Downtown office tower",
        }
        db = AsyncMock()
        with (
            patch(
                "app.services.similar_listings.get_property_by_id",
                new_callable=AsyncMock,
                return_value=seed,
            ),
            patch(
                "app.services.similar_listings.list_similar_candidate_rows",
                new_callable=AsyncMock,
                return_value=[far, near],
            ),
            patch(
                "app.services.similar_listings.embed",
                new_callable=AsyncMock,
                return_value=[
                    [1.0, 0.0],
                    [0.0, 1.0],
                    [0.9, 0.1],
                ],
            ),
        ):
            result = await find_similar_listings(db, seed_id, limit=2)

        assert result is not None
        assert len(result) == 2
        assert result[0][0]["id"] == near_id
        assert result[0][1] > result[1][1]
        assert result[1][0]["id"] == far_id

    async def test_embeddings_unavailable_propagates(self):
        seed_id = uuid4()
        seed = {"id": seed_id, "state": "TX", "description": "Warehouse"}
        db = AsyncMock()
        with (
            patch(
                "app.services.similar_listings.get_property_by_id",
                new_callable=AsyncMock,
                return_value=seed,
            ),
            patch(
                "app.services.similar_listings.list_similar_candidate_rows",
                new_callable=AsyncMock,
                return_value=[{"id": uuid4(), "description": "Other"}],
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
