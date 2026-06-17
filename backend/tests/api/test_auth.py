"""Tests for POST /api/v1/sign-in and POST /api/v1/sign-up."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from supabase import AuthApiError, AuthInvalidCredentialsError, AuthWeakPasswordError


def _make_session(user_id: str = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"):
    user = MagicMock()
    user.id = user_id
    user.email = "user@example.com"

    session = MagicMock()
    session.user = user
    session.access_token = "access-tok"
    session.refresh_token = "refresh-tok"
    session.expires_in = 3600
    session.token_type = "bearer"

    result = MagicMock()
    result.session = session
    return result


def _make_created_user(user_id: str = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"):
    user = MagicMock()
    user.id = user_id
    user.email = "new@example.com"
    user.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)

    result = MagicMock()
    result.user = user
    return result


_SIGN_IN = {"email": "user@example.com", "password": "securepass"}
_SIGN_UP = {
    "email": "new@example.com",
    "password": "securepass",
    "first_name": "Alice",
    "last_name": "Smith",
}


class TestSignIn:
    async def test_success_returns_tokens(self, client, mock_supabase):
        mock_supabase.auth.sign_in_with_password = AsyncMock(return_value=_make_session())
        r = await client.post("/api/v1/auth/sign-in", json=_SIGN_IN)
        assert r.status_code == 200
        body = r.json()
        assert body["access_token"] == "access-tok"
        assert body["user"]["email"] == "user@example.com"

    async def test_invalid_credentials_returns_401(self, client, mock_supabase):
        mock_supabase.auth.sign_in_with_password = AsyncMock(
            side_effect=AuthInvalidCredentialsError("Invalid credentials")
        )
        r = await client.post("/api/v1/auth/sign-in", json=_SIGN_IN)
        assert r.status_code == 401

    async def test_auth_api_error_invalid_grant_returns_401(self, client, mock_supabase):
        exc = AuthApiError("bad", status=400, code="invalid_credentials")
        mock_supabase.auth.sign_in_with_password = AsyncMock(side_effect=exc)
        r = await client.post("/api/v1/auth/sign-in", json=_SIGN_IN)
        assert r.status_code == 401

    async def test_email_not_confirmed_returns_403(self, client, mock_supabase):
        exc = AuthApiError("Email not confirmed", status=400, code="email_not_confirmed")
        mock_supabase.auth.sign_in_with_password = AsyncMock(side_effect=exc)
        r = await client.post("/api/v1/auth/sign-in", json=_SIGN_IN)
        assert r.status_code == 403

    async def test_transport_error_returns_503(self, client, mock_supabase):
        mock_supabase.auth.sign_in_with_password = AsyncMock(
            side_effect=httpx.ConnectError("timeout")
        )
        r = await client.post("/api/v1/auth/sign-in", json=_SIGN_IN)
        assert r.status_code == 503

    async def test_no_session_returns_403(self, client, mock_supabase):
        result = MagicMock()
        result.session = None
        mock_supabase.auth.sign_in_with_password = AsyncMock(return_value=result)
        r = await client.post("/api/v1/auth/sign-in", json=_SIGN_IN)
        assert r.status_code == 403

    async def test_invalid_body_returns_422(self, client):
        r = await client.post("/api/v1/auth/sign-in", json={"email": "bad"})
        assert r.status_code == 422


class TestSignUp:
    async def test_success_returns_201(self, client, mock_supabase):
        mock_supabase.auth.admin.create_user = AsyncMock(return_value=_make_created_user())
        with patch(
            "app.api.v1.endpoints.auth.sign_up.upsert_profile_patch",
            new_callable=AsyncMock,
        ):
            r = await client.post("/api/v1/auth/sign-up", json=_SIGN_UP)
        assert r.status_code == 201
        assert r.json()["email"] == "new@example.com"

    async def test_email_already_exists_returns_409(self, client, mock_supabase):
        exc = AuthApiError("exists", status=400, code="email_exists")
        mock_supabase.auth.admin.create_user = AsyncMock(side_effect=exc)
        r = await client.post("/api/v1/auth/sign-up", json=_SIGN_UP)
        assert r.status_code == 409

    async def test_weak_password_sdk_returns_422(self, client, mock_supabase):
        exc = AuthWeakPasswordError("Too weak", status=422, reasons=["too short"])
        mock_supabase.auth.admin.create_user = AsyncMock(side_effect=exc)
        r = await client.post("/api/v1/auth/sign-up", json=_SIGN_UP)
        assert r.status_code == 422

    async def test_weak_password_api_returns_422(self, client, mock_supabase):
        exc = AuthApiError("Too weak", status=400, code="weak_password")
        mock_supabase.auth.admin.create_user = AsyncMock(side_effect=exc)
        r = await client.post("/api/v1/auth/sign-up", json=_SIGN_UP)
        assert r.status_code == 422

    async def test_invalid_body_returns_422(self, client):
        r = await client.post("/api/v1/auth/sign-up", json={"email": "x@x.com", "password": "pass"})
        assert r.status_code == 422
