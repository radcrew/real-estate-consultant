"""Tests for outreach draft endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

_DRAFT_UUID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
_PROP_UUID = "b2c3d4e5-f6a7-8901-bcde-f12345678901"

_DRAFT_ROW = {
    "id": _DRAFT_UUID,
    "property_id": _PROP_UUID,
    "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "draft_email": "Dear broker,\nI am interested in your property...",
    "created_at": "2024-01-01T00:00:00+00:00",
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


class TestCreateOutreachDraft:
    async def test_success_returns_draft(self, client):
        with (
            patch("app.api.v1.endpoints.outreach.router.get_property_by_id", new_callable=AsyncMock, return_value=_PROPERTY_ROW),
            patch("app.api.v1.endpoints.outreach.router.fetch_profile_row", new_callable=AsyncMock, return_value=None),
            patch("app.api.v1.endpoints.outreach.router.generate_broker_outreach_draft", new_callable=AsyncMock, return_value="Dear broker..."),
            patch("app.api.v1.endpoints.outreach.router.insert_outreach_draft", new_callable=AsyncMock, return_value=_DRAFT_ROW),
        ):
            r = await client.post("/api/v1/outreach/drafts", json={"property_id": _PROP_UUID})
        assert r.status_code == 200
        assert r.json()["draft_email"] == "Dear broker,\nI am interested in your property..."

    async def test_property_not_found_returns_404(self, client):
        with patch("app.api.v1.endpoints.outreach.router.get_property_by_id", new_callable=AsyncMock, return_value=None):
            r = await client.post("/api/v1/outreach/drafts", json={"property_id": _PROP_UUID})
        assert r.status_code == 404


class TestGetLatestOutreachDraft:
    async def test_returns_draft(self, client):
        with patch(
            "app.api.v1.endpoints.outreach.router.fetch_latest_outreach_draft_for_property",
            new_callable=AsyncMock,
            return_value=_DRAFT_ROW,
        ):
            r = await client.get(f"/api/v1/outreach/drafts/latest?property_id={_PROP_UUID}")
        assert r.status_code == 200
        assert r.json()["id"] == _DRAFT_UUID

    async def test_not_found_returns_404(self, client):
        with patch(
            "app.api.v1.endpoints.outreach.router.fetch_latest_outreach_draft_for_property",
            new_callable=AsyncMock,
            return_value=None,
        ):
            r = await client.get(f"/api/v1/outreach/drafts/latest?property_id={_PROP_UUID}")
        assert r.status_code == 404


class TestGetOutreachDraft:
    async def test_returns_draft(self, client):
        with patch(
            "app.api.v1.endpoints.outreach.router.fetch_outreach_draft_for_user",
            new_callable=AsyncMock,
            return_value=_DRAFT_ROW,
        ):
            r = await client.get(f"/api/v1/outreach/drafts/{_DRAFT_UUID}")
        assert r.status_code == 200

    async def test_not_found_returns_404(self, client):
        with patch(
            "app.api.v1.endpoints.outreach.router.fetch_outreach_draft_for_user",
            new_callable=AsyncMock,
            return_value=None,
        ):
            r = await client.get(f"/api/v1/outreach/drafts/{_DRAFT_UUID}")
        assert r.status_code == 404


class TestPatchOutreachDraft:
    async def test_success_returns_updated_draft(self, client):
        updated = {**_DRAFT_ROW, "draft_email": "Updated text"}
        with patch(
            "app.api.v1.endpoints.outreach.router.update_outreach_draft_email",
            new_callable=AsyncMock,
            return_value=updated,
        ):
            r = await client.patch(
                f"/api/v1/outreach/drafts/{_DRAFT_UUID}",
                json={"draft_email": "Updated text"},
            )
        assert r.status_code == 200
        assert r.json()["draft_email"] == "Updated text"

    async def test_not_found_returns_404(self, client):
        with patch(
            "app.api.v1.endpoints.outreach.router.update_outreach_draft_email",
            new_callable=AsyncMock,
            return_value=None,
        ):
            r = await client.patch(
                f"/api/v1/outreach/drafts/{_DRAFT_UUID}",
                json={"draft_email": "Updated text"},
            )
        assert r.status_code == 404
