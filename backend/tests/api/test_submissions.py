"""Tests for listing-submissions endpoints (public create, admin list/patch)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_VALID_SUBMISSION = {
    "property_type": "Industrial",
    "listing_type": "ForSale",
    "title": "Warehouse on Main",
    "city": "Austin",
    "state": "TX",
    "contact_name": "Alice",
    "contact_email": "alice@example.com",
}

_SUBMISSION_ROW = {
    "id": "sub-uuid-1234",
    "status": "pending",
    "property_type": "Industrial",
    "listing_type": "ForSale",
    "title": "Warehouse on Main",
    "city": "Austin",
    "state": "TX",
    "contact_name": "Alice",
    "contact_email": "alice@example.com",
    "created_at": "2024-01-01T00:00:00",
}


class TestSubmitListing:
    async def test_success_returns_201(self, client):
        with patch(
            "app.api.v1.endpoints.submissions.create_listing_submission",
            new_callable=AsyncMock,
            return_value={"id": "sub-uuid-1234", "status": "pending"},
        ):
            r = await client.post("/api/v1/listing-submissions", json=_VALID_SUBMISSION)
        assert r.status_code == 201
        body = r.json()
        assert body["id"] == "sub-uuid-1234"
        assert body["status"] == "pending"

    async def test_invalid_body_returns_422(self, client):
        r = await client.post("/api/v1/listing-submissions", json={"title": "missing fields"})
        assert r.status_code == 422

    async def test_invalid_email_returns_422(self, client):
        r = await client.post(
            "/api/v1/listing-submissions",
            json={**_VALID_SUBMISSION, "contact_email": "not-email"},
        )
        assert r.status_code == 422
