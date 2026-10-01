"""Tests for POST /api/v1/auth/sign-in and POST /api/v1/auth/sign-up."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from botocore.exceptions import ClientError, EndpointConnectionError

from supabase import AuthApiError, AuthInvalidCredentialsError


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


_NEW_SUB = "6f1c2a9e-0000-4000-8000-000000000002"


def _client_error(code: str, message: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": message}}, "SignUp")


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
    @pytest.fixture
    def idp(self):
        idp = MagicMock()
        idp.sign_up.return_value = {"UserSub": _NEW_SUB, "UserConfirmed": False}
        with patch("app.api.v1.endpoints.auth.sign_up.get_idp_client", return_value=idp):
            yield idp

    @pytest.fixture
    def upsert(self):
        with patch(
            "app.api.v1.endpoints.auth.sign_up.upsert_profile_patch",
            new_callable=AsyncMock,
        ) as mock:
            yield mock

    async def test_success_returns_201_and_needs_confirmation(self, client, idp, upsert):
        r = await client.post("/api/v1/auth/sign-up", json=_SIGN_UP)
        assert r.status_code == 201
        assert r.json() == {
            "id": _NEW_SUB,
            "email": "new@example.com",
            "confirmation_required": True,
        }

    async def test_sends_names_as_cognito_attributes(self, client, idp, upsert):
        await client.post("/api/v1/auth/sign-up", json=_SIGN_UP)
        kwargs = idp.sign_up.call_args.kwargs
        assert kwargs["Username"] == "new@example.com"
        assert {"Name": "given_name", "Value": "Alice"} in kwargs["UserAttributes"]
        assert {"Name": "family_name", "Value": "Smith"} in kwargs["UserAttributes"]
        assert kwargs["SecretHash"]

    async def test_profile_row_is_keyed_by_cognito_sub(self, client, idp, upsert):
        await client.post("/api/v1/auth/sign-up", json=_SIGN_UP)
        user_id, patch_body = upsert.call_args.args[1:]
        assert str(user_id) == _NEW_SUB
        assert patch_body.first_name == "Alice"
        assert patch_body.email == "new@example.com"

    async def test_email_already_exists_returns_409(self, client, idp, upsert):
        idp.sign_up.side_effect = _client_error("UsernameExistsException", "exists")
        r = await client.post("/api/v1/auth/sign-up", json=_SIGN_UP)
        assert r.status_code == 409
        upsert.assert_not_called()

    async def test_weak_password_returns_422_with_cognito_message(self, client, idp, upsert):
        idp.sign_up.side_effect = _client_error(
            "InvalidPasswordException", "Password must have uppercase characters"
        )
        r = await client.post("/api/v1/auth/sign-up", json=_SIGN_UP)
        assert r.status_code == 422
        assert "uppercase" in r.json()["detail"]

    async def test_throttled_returns_429(self, client, idp, upsert):
        idp.sign_up.side_effect = _client_error("TooManyRequestsException", "slow down")
        r = await client.post("/api/v1/auth/sign-up", json=_SIGN_UP)
        assert r.status_code == 429

    async def test_unreachable_cognito_returns_503(self, client, idp, upsert):
        idp.sign_up.side_effect = EndpointConnectionError(endpoint_url="https://cognito-idp")
        r = await client.post("/api/v1/auth/sign-up", json=_SIGN_UP)
        assert r.status_code == 503

    async def test_invalid_body_returns_422(self, client):
        r = await client.post("/api/v1/auth/sign-up", json={"email": "x@x.com", "password": "pass"})
        assert r.status_code == 422
