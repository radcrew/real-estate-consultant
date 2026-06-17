"""Tests for admin listing-submission routes (GET list, PATCH status)."""
from unittest.mock import AsyncMock, patch

import pytest
from app.core.deps import get_current_admin

_ITEM = {
    "id": "sub-1",
    "status": "pending",
    "property_type": "Industrial",
    "listing_type": "ForSale",
    "title": "Warehouse",
    "city": "Austin",
    "state": "TX",
    "contact_name": "Alice",
    "contact_email": "alice@example.com",
    "created_at": "2024-01-01T00:00:00",
}


@pytest.fixture
async def admin_client(mock_db, mock_supabase, mock_user):
    from httpx import ASGITransport, AsyncClient
    from app.core.database import get_session
    from app.core.supabase_sdk import get_supabase_sdk_client
    from app.core.deps import get_current_user
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[get_session] = lambda: mock_db
    app.dependency_overrides[get_supabase_sdk_client] = lambda: mock_supabase
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_current_admin] = lambda: mock_user
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


class TestListSubmissions:
    async def test_returns_list(self, admin_client):
        with patch(
            "app.api.v1.endpoints.submissions.list_listing_submissions",
            new_callable=AsyncMock,
            return_value=[_ITEM],
        ):
            r = await admin_client.get("/api/v1/listing-submissions")
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["status"] == "pending"

    async def test_returns_empty_list(self, admin_client):
        with patch(
            "app.api.v1.endpoints.submissions.list_listing_submissions",
            new_callable=AsyncMock,
            return_value=[],
        ):
            r = await admin_client.get("/api/v1/listing-submissions")
        assert r.status_code == 200
        assert r.json() == []


class TestPatchSubmission:
    async def test_approve_returns_updated(self, admin_client):
        updated = {**_ITEM, "status": "approved"}
        with patch(
            "app.api.v1.endpoints.submissions.update_submission_status",
            new_callable=AsyncMock,
            return_value=updated,
        ):
            r = await admin_client.patch(
                "/api/v1/listing-submissions/sub-1",
                json={"status": "approved"},
            )
        assert r.status_code == 200
        assert r.json()["status"] == "approved"

    async def test_not_found_returns_404(self, admin_client):
        with patch(
            "app.api.v1.endpoints.submissions.update_submission_status",
            new_callable=AsyncMock,
            return_value=None,
        ):
            r = await admin_client.patch(
                "/api/v1/listing-submissions/sub-1",
                json={"status": "rejected"},
            )
        assert r.status_code == 404

    async def test_invalid_status_returns_422(self, admin_client):
        r = await admin_client.patch(
            "/api/v1/listing-submissions/sub-1",
            json={"status": "unknown"},
        )
        assert r.status_code == 422
