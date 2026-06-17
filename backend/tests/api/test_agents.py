"""Tests for GET /api/v1/agents/{broker}."""
from unittest.mock import AsyncMock, patch

import pytest

_ROW = {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
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
    "listing_broker_name": "Bob Jones",
    "listing_broker_email": "bob@example.com",
    "listing_broker_phone": "555-1234",
}


class TestGetAgent:
    async def test_returns_agent_profile(self, client):
        with patch(
            "app.api.v1.endpoints.agents.list_properties_by_broker",
            new_callable=AsyncMock,
            return_value=[_ROW],
        ):
            r = await client.get("/api/v1/agents/bob-jones")
        assert r.status_code == 200
        body = r.json()
        assert body["name"] == "Bob Jones"
        assert body["email"] == "bob@example.com"
        assert len(body["properties"]) == 1

    async def test_not_found_returns_404(self, client):
        with patch(
            "app.api.v1.endpoints.agents.list_properties_by_broker",
            new_callable=AsyncMock,
            return_value=[],
        ):
            r = await client.get("/api/v1/agents/unknown-broker")
        assert r.status_code == 404

    async def test_multiple_properties(self, client):
        row2 = {**_ROW, "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901", "city": "Dallas"}
        with patch(
            "app.api.v1.endpoints.agents.list_properties_by_broker",
            new_callable=AsyncMock,
            return_value=[_ROW, row2],
        ):
            r = await client.get("/api/v1/agents/bob-jones")
        assert r.status_code == 200
        assert len(r.json()["properties"]) == 2

    async def test_falls_back_to_broker_param_when_no_name(self, client):
        row = {**_ROW, "listing_broker_name": None}
        with patch(
            "app.api.v1.endpoints.agents.list_properties_by_broker",
            new_callable=AsyncMock,
            return_value=[row],
        ):
            r = await client.get("/api/v1/agents/fallback-name")
        assert r.status_code == 200
        assert r.json()["name"] == "fallback-name"
