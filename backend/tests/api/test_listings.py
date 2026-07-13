"""Tests for public listings endpoints."""
from unittest.mock import AsyncMock, patch

import pytest


_PROPERTY_ROW = {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "address": "100 Main St",
    "city": "Austin",
    "state": "TX",
    "country": "US",
    "latitude": 30.2,
    "longitude": -97.7,
    "property_type": "Industrial",
    "listing_type": "PropertyForSale",
    "description": "A great warehouse",
    "size_sqft": 10000,
    "price": 1_500_000,
    "rent": None,
    "clear_height": 32.0,
    "loading_docks": 4,
    "listing_broker_name": "Alice",
    "listing_broker_email": "alice@example.com",
    "listing_broker_phone": "555-0100",
}


class TestFeaturedListings:
    async def test_returns_empty_list_when_no_rows(self, client):
        with patch(
            "app.api.v1.endpoints.listings.featured.list_featured_property_rows",
            new_callable=AsyncMock,
            return_value=[],
        ):
            r = await client.get("/api/v1/listings/featured")
        assert r.status_code == 200
        assert r.json() == {"listings": []}

    async def test_returns_listing_with_image(self, client):
        with (
            patch(
                "app.api.v1.endpoints.listings.featured.list_featured_property_rows",
                new_callable=AsyncMock,
                return_value=[_PROPERTY_ROW],
            ),
            patch(
                "app.api.v1.endpoints.listings.featured.get_first_image_url",
                new_callable=AsyncMock,
                return_value="https://example.com/img.jpg",
            ),
        ):
            r = await client.get("/api/v1/listings/featured")
        assert r.status_code == 200
        body = r.json()
        assert len(body["listings"]) == 1
        listing = body["listings"][0]
        assert listing["images"] == ["https://example.com/img.jpg"]
        assert listing["property"]["city"] == "Austin"
        assert listing["property"]["listing_type"] == "Property for sale"

    async def test_returns_listing_without_image(self, client):
        with (
            patch(
                "app.api.v1.endpoints.listings.featured.list_featured_property_rows",
                new_callable=AsyncMock,
                return_value=[_PROPERTY_ROW],
            ),
            patch(
                "app.api.v1.endpoints.listings.featured.get_first_image_url",
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            r = await client.get("/api/v1/listings/featured")
        assert r.status_code == 200
        body = r.json()
        assert body["listings"][0]["images"] == []

    async def test_multiple_listings_returned(self, client):
        row2 = {**_PROPERTY_ROW, "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901", "city": "Dallas"}
        with (
            patch(
                "app.api.v1.endpoints.listings.featured.list_featured_property_rows",
                new_callable=AsyncMock,
                return_value=[_PROPERTY_ROW, row2],
            ),
            patch(
                "app.api.v1.endpoints.listings.featured.get_first_image_url",
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            r = await client.get("/api/v1/listings/featured")
        assert r.status_code == 200
        assert len(r.json()["listings"]) == 2
