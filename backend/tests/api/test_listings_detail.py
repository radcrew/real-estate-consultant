"""Tests for GET /api/v1/listings/{property_id}."""
from unittest.mock import AsyncMock, patch

import pytest

_UUID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

_ROW = {
    "id": _UUID,
    "address": "100 Main St",
    "city": "Austin",
    "state": "TX",
    "country": "US",
    "latitude": 30.2,
    "longitude": -97.7,
    "property_type": "Industrial",
    "listing_type": "PropertyForSale",
    "description": "A warehouse",
    "size_sqft": 10000,
    "price": 1_500_000,
    "rent": None,
    "clear_height": 32.0,
    "loading_docks": 4,
    "listing_broker_name": "Alice",
    "listing_broker_email": "alice@example.com",
    "listing_broker_phone": "555-0100",
}


class TestGetListingDetail:
    async def test_returns_listing_with_images(self, client):
        with (
            patch(
                "app.api.v1.endpoints.listings.router.get_property_by_id",
                new_callable=AsyncMock,
                return_value=_ROW,
            ),
            patch(
                "app.api.v1.endpoints.listings.router.list_all_image_urls",
                new_callable=AsyncMock,
                return_value=["https://example.com/img1.jpg", "https://example.com/img2.jpg"],
            ),
        ):
            r = await client.get(f"/api/v1/listings/{_UUID}")
        assert r.status_code == 200
        body = r.json()
        assert body["property"]["city"] == "Austin"
        assert body["property"]["listing_type"] == "Property for sale"
        assert body["images"] == ["https://example.com/img1.jpg", "https://example.com/img2.jpg"]

    async def test_returns_listing_with_no_images(self, client):
        with (
            patch(
                "app.api.v1.endpoints.listings.router.get_property_by_id",
                new_callable=AsyncMock,
                return_value=_ROW,
            ),
            patch(
                "app.api.v1.endpoints.listings.router.list_all_image_urls",
                new_callable=AsyncMock,
                return_value=[],
            ),
        ):
            r = await client.get(f"/api/v1/listings/{_UUID}")
        assert r.status_code == 200
        assert r.json()["images"] == []

    async def test_not_found_returns_404(self, client):
        with patch(
            "app.api.v1.endpoints.listings.router.get_property_by_id",
            new_callable=AsyncMock,
            return_value=None,
        ):
            r = await client.get(f"/api/v1/listings/{_UUID}")
        assert r.status_code == 404

    async def test_invalid_uuid_returns_422(self, client):
        r = await client.get("/api/v1/listings/not-a-uuid")
        assert r.status_code == 422
