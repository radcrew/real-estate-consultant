"""Tests for account profile, password, and saved listings endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_UID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
_PROP_UUID = "b2c3d4e5-f6a7-8901-bcde-f12345678901"


def _make_auth_user(email: str = "user@example.com"):
    from supabase_auth.types import User
    return User(
        id=_UID,
        app_metadata={},
        user_metadata={},
        aud="authenticated",
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        email=email,
    )


class TestGetAccountProfile:
    async def test_returns_profile(self, client, mock_user):
        with patch(
            "app.api.v1.endpoints.account.profile.get_profile_row",
            new_callable=AsyncMock,
            return_value={"id": _UID, "first_name": "Alice", "last_name": "Smith"},
        ):
            r = await client.get("/api/v1/account/profile")
        assert r.status_code == 200
        body = r.json()
        assert body["email"] == "user@example.com"
        assert body["first_name"] == "Alice"

    async def test_profile_row_none_returns_minimal(self, client):
        with patch(
            "app.api.v1.endpoints.account.profile.get_profile_row",
            new_callable=AsyncMock,
            return_value=None,
        ):
            r = await client.get("/api/v1/account/profile")
        assert r.status_code == 200
        assert r.json()["first_name"] is None

    async def test_does_not_call_admin_api(self, client):
        """GET must not re-fetch the auth user via the Admin API — that call is a
        redundant network round-trip and was the source of intermittent 503s."""
        with (
            patch(
                "app.api.v1.endpoints.account.profile.get_auth_user",
                new_callable=AsyncMock,
            ) as mock_get_auth_user,
            patch(
                "app.api.v1.endpoints.account.profile.get_profile_row",
                new_callable=AsyncMock,
                return_value=None,
            ),
        ):
            r = await client.get("/api/v1/account/profile")
        assert r.status_code == 200
        mock_get_auth_user.assert_not_called()


class TestUpdateAccountProfile:
    async def test_success_returns_updated_profile(self, client):
        auth_user = _make_auth_user()
        with (
            patch("app.api.v1.endpoints.account.profile.upsert_profile_patch", new_callable=AsyncMock),
            patch("app.api.v1.endpoints.account.profile.update_auth_user", new_callable=AsyncMock),
            patch(
                "app.api.v1.endpoints.account.profile.get_auth_user",
                new_callable=AsyncMock,
                return_value=auth_user,
            ),
            patch(
                "app.api.v1.endpoints.account.profile.get_profile_row",
                new_callable=AsyncMock,
                return_value={"id": _UID, "first_name": "Bob"},
            ),
        ):
            r = await client.patch("/api/v1/account/profile", json={"first_name": "Bob"})
        assert r.status_code == 200
        assert r.json()["first_name"] == "Bob"

    async def test_empty_body_returns_400(self, client):
        r = await client.patch("/api/v1/account/profile", json={})
        assert r.status_code == 400


class TestChangePassword:
    async def test_success_returns_204(self, client, mock_user):
        mock_user.email = "user@example.com"
        with (
            patch("app.api.v1.endpoints.account.password.verify_current_email_password", new_callable=AsyncMock),
            patch("app.api.v1.endpoints.account.password.update_auth_user_password", new_callable=AsyncMock),
        ):
            r = await client.post(
                "/api/v1/account/account/password",
                json={"current_password": "oldpass1", "new_password": "newpass1"},
            )
        assert r.status_code == 204

    async def test_same_password_returns_422(self, client, mock_user):
        mock_user.email = "user@example.com"
        r = await client.post(
            "/api/v1/account/account/password",
            json={"current_password": "samepass", "new_password": "samepass"},
        )
        assert r.status_code == 422

    async def test_no_email_returns_400(self, client, mock_user):
        mock_user.email = ""
        r = await client.post(
            "/api/v1/account/account/password",
            json={"current_password": "oldpass1", "new_password": "newpass1"},
        )
        assert r.status_code == 400


class TestSavedListings:
    async def test_get_saved_returns_ids(self, client, mock_user):
        with patch(
            "app.api.v1.endpoints.account.saved.list_saved_property_ids",
            new_callable=AsyncMock,
            return_value=[_PROP_UUID],
        ):
            r = await client.get("/api/v1/account/saved")
        assert r.status_code == 200
        assert r.json()["property_ids"] == [_PROP_UUID]

    async def test_save_listing_returns_204(self, client, mock_user):
        with patch(
            "app.api.v1.endpoints.account.saved.add_saved_listing",
            new_callable=AsyncMock,
        ):
            r = await client.post("/api/v1/account/saved", json={"property_id": _PROP_UUID})
        assert r.status_code == 204

    async def test_unsave_listing_returns_204(self, client, mock_user):
        with patch(
            "app.api.v1.endpoints.account.saved.remove_saved_listing",
            new_callable=AsyncMock,
        ):
            r = await client.delete(f"/api/v1/account/saved/{_PROP_UUID}")
        assert r.status_code == 204
