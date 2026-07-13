"""Tests for search endpoints."""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_PROFILE_UUID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
_SESSION_UUID = "b2c3d4e5-f6a7-8901-bcde-f12345678901"
_PROP_UUID = "c3d4e5f6-a7b8-9012-cdef-123456789012"

_SESSION_ROW = {
    "id": _SESSION_UUID,
    "status": "in_progress",
    "search_profile_id": _PROFILE_UUID,
    "criteria": {"location": "Austin"},
}

_PROPERTY_ROW = {
    "id": _PROP_UUID,
    "address": "100 Main St",
    "city": "Austin",
    "state": "TX",
    "country": "US",
    "latitude": 30.2,
    "longitude": -97.7,
    "property_type": "Industrial",
    "listing_type": "PropertyForSale",
    "description": None,
    "size_sqft": 5000,
    "price": 800_000,
    "rent": None,
    "clear_height": None,
    "loading_docks": None,
    "listing_broker_name": "Bob",
    "listing_broker_email": "bob@example.com",
    "listing_broker_phone": None,
}


class TestQuickSearch:
    async def test_success_returns_search_profile_id(self, client):
        with (
            patch("app.api.v1.endpoints.search.router.create_search_profile", new_callable=AsyncMock, return_value=uuid.UUID(_PROFILE_UUID)),
            patch("app.api.v1.endpoints.search.router.create_intake_session_row", new_callable=AsyncMock, return_value=MagicMock(id=uuid.UUID(_SESSION_UUID))),
            patch("app.api.v1.endpoints.search.router.save_intake_criteria", new_callable=AsyncMock),
            patch("app.api.v1.endpoints.search.router.update_intake_session_completed", new_callable=AsyncMock),
        ):
            r = await client.post("/api/v1/search/quick", json={"location": "Austin", "property_types": ["industrial"], "price_min": 100000})
        assert r.status_code == 200
        assert r.json()["search_profile_id"] == _PROFILE_UUID

    async def test_empty_body_still_creates_profile(self, client):
        with (
            patch("app.api.v1.endpoints.search.router.create_search_profile", new_callable=AsyncMock, return_value=uuid.UUID(_PROFILE_UUID)),
            patch("app.api.v1.endpoints.search.router.create_intake_session_row", new_callable=AsyncMock, return_value=MagicMock(id=uuid.UUID(_SESSION_UUID))),
            patch("app.api.v1.endpoints.search.router.save_intake_criteria", new_callable=AsyncMock),
            patch("app.api.v1.endpoints.search.router.update_intake_session_completed", new_callable=AsyncMock),
        ):
            r = await client.post("/api/v1/search/quick", json={})
        assert r.status_code == 200


class TestSearchListings:
    async def test_returns_results(self, client):
        from app.schemas.search import CriteriaFieldItem
        criteria_field = CriteriaFieldItem(type="location", label="Location", unit=None, data="Austin")

        with (
            patch("app.api.v1.endpoints.search.router.ensure_search_profile_access", new_callable=AsyncMock),
            patch("app.api.v1.endpoints.search.router.get_profile_session_row", new_callable=AsyncMock, return_value=_SESSION_ROW),
            patch("app.api.v1.endpoints.search.router.search_properties", new_callable=AsyncMock, return_value=([(_PROPERTY_ROW, 85.0)], 1)),
            patch("app.api.v1.endpoints.search.router.get_first_image_url", new_callable=AsyncMock, return_value=None),
            patch("app.api.v1.endpoints.search.router.normalize_criteria", new_callable=AsyncMock, return_value={"location": criteria_field}),
        ):
            r = await client.get(f"/api/v1/search/{_PROFILE_UUID}")
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 1
        assert len(body["results"]) == 1
        assert body["results"][0]["match_score"] == 85.0

    async def test_empty_results(self, client):
        with (
            patch("app.api.v1.endpoints.search.router.ensure_search_profile_access", new_callable=AsyncMock),
            patch("app.api.v1.endpoints.search.router.get_profile_session_row", new_callable=AsyncMock, return_value=_SESSION_ROW),
            patch("app.api.v1.endpoints.search.router.search_properties", new_callable=AsyncMock, return_value=([], 0)),
            patch("app.api.v1.endpoints.search.router.normalize_criteria", new_callable=AsyncMock, return_value={}),
        ):
            r = await client.get(f"/api/v1/search/{_PROFILE_UUID}")
        assert r.status_code == 200
        assert r.json()["total"] == 0
        assert r.json()["results"] == []


class TestUpdateSearchCriteria:
    async def test_success_returns_updated_criteria(self, client):
        from app.models.intake_sessions import IntakeSession
        session = IntakeSession(id=uuid.UUID(_SESSION_UUID), status="in_progress")

        from app.schemas.search import CriteriaFieldItem
        criteria_field = CriteriaFieldItem(type="location", label="Location", unit=None, data="Dallas")

        with (
            patch("app.api.v1.endpoints.search.router.ensure_search_profile_access", new_callable=AsyncMock),
            patch("app.api.v1.endpoints.search.router.get_profile_session_row", new_callable=AsyncMock, return_value=_SESSION_ROW),
            patch("app.api.v1.endpoints.search.router.save_intake_criteria", new_callable=AsyncMock, return_value=_SESSION_ROW),
            patch("app.api.v1.endpoints.search.router.parse_intake_session", return_value=session),
            patch("app.api.v1.endpoints.search.router.normalize_criteria", new_callable=AsyncMock, return_value={"location": criteria_field}),
        ):
            r = await client.put(f"/api/v1/search/{_PROFILE_UUID}", json={"location": "Dallas"})
        assert r.status_code == 200


class TestExplainFit:
    async def test_returns_explanation(self, client):
        from app.llm.fit.schema import FitExplanationLLM

        parsed = FitExplanationLLM(
            summary="This listing is in Austin, matching your target city.",
            strengths=["Right city"],
            considerations=[],
        )
        breakdown = (_PROPERTY_ROW, (1.0, 0.8, 0.6, 82.0))

        with (
            patch("app.api.v1.endpoints.search.fit.ensure_search_profile_access", new_callable=AsyncMock),
            patch("app.api.v1.endpoints.search.fit.get_profile_session_row", new_callable=AsyncMock, return_value=_SESSION_ROW),
            patch("app.api.v1.endpoints.search.fit.get_property_match_breakdown", new_callable=AsyncMock, return_value=breakdown),
            patch("app.api.v1.endpoints.search.fit.generate_fit_explanation", new_callable=AsyncMock, return_value=parsed),
        ):
            r = await client.post(f"/api/v1/search/{_PROFILE_UUID}/fit/{_PROP_UUID}")
        assert r.status_code == 200
        body = r.json()
        assert body["property_id"] == _PROP_UUID
        assert body["score"] == {"location": 1.0, "price": 0.8, "size": 0.6, "total": 82.0}
        assert body["summary"] == parsed.summary
        assert body["strengths"] == ["Right city"]
        assert body["considerations"] == []

    async def test_unknown_property_returns_404(self, client):
        with (
            patch("app.api.v1.endpoints.search.fit.ensure_search_profile_access", new_callable=AsyncMock),
            patch("app.api.v1.endpoints.search.fit.get_profile_session_row", new_callable=AsyncMock, return_value=_SESSION_ROW),
            patch("app.api.v1.endpoints.search.fit.get_property_match_breakdown", new_callable=AsyncMock, return_value=None),
        ):
            r = await client.post(f"/api/v1/search/{_PROFILE_UUID}/fit/{_PROP_UUID}")
        assert r.status_code == 404
