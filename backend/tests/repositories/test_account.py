from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastapi import HTTPException
from supabase import AuthApiError, AuthInvalidCredentialsError, AuthWeakPasswordError

from app.repositories.account import (
    get_auth_user,
    update_auth_user,
    update_auth_user_password,
    verify_current_email_password,
)

_USER_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"


def _client_with_auth() -> MagicMock:
    client = MagicMock()
    client.auth = MagicMock()
    client.auth.admin = MagicMock()
    return client


class TestVerifyCurrentEmailPassword:
    async def test_succeeds_with_correct_password(self):
        client = _client_with_auth()
        client.auth.sign_in_with_password = AsyncMock(return_value=None)
        await verify_current_email_password(client, email="u@example.com", password="secret123")
        client.auth.sign_in_with_password.assert_called_once_with(
            {"email": "u@example.com", "password": "secret123"},
        )

    async def test_invalid_credentials_raises_401(self):
        client = _client_with_auth()
        client.auth.sign_in_with_password = AsyncMock(
            side_effect=AuthInvalidCredentialsError("bad creds"),
        )
        with pytest.raises(HTTPException) as info:
            await verify_current_email_password(client, email="u@example.com", password="wrong")
        assert info.value.status_code == 401

    async def test_invalid_grant_raises_401(self):
        client = _client_with_auth()
        client.auth.sign_in_with_password = AsyncMock(
            side_effect=AuthApiError("bad", status=400, code="invalid_grant"),
        )
        with pytest.raises(HTTPException) as info:
            await verify_current_email_password(client, email="u@example.com", password="wrong")
        assert info.value.status_code == 401

    async def test_other_auth_api_error_raises_503(self):
        client = _client_with_auth()
        client.auth.sign_in_with_password = AsyncMock(
            side_effect=AuthApiError("down", status=500, code="unexpected_failure"),
        )
        with pytest.raises(HTTPException) as info:
            await verify_current_email_password(client, email="u@example.com", password="x")
        assert info.value.status_code == 503

    async def test_transport_error_raises_503(self):
        client = _client_with_auth()
        client.auth.sign_in_with_password = AsyncMock(
            side_effect=httpx.ConnectError("no network"),
        )
        with pytest.raises(HTTPException) as info:
            await verify_current_email_password(client, email="u@example.com", password="x")
        assert info.value.status_code == 503


class TestGetAuthUser:
    async def test_returns_user(self):
        client = _client_with_auth()
        fake_user = MagicMock(id=_USER_ID)
        client.auth.admin.get_user_by_id = AsyncMock(return_value=MagicMock(user=fake_user))
        result = await get_auth_user(client, _USER_ID)
        assert result is fake_user

    async def test_auth_api_error_raises_503(self):
        client = _client_with_auth()
        client.auth.admin.get_user_by_id = AsyncMock(
            side_effect=AuthApiError("missing", status=404, code="user_not_found"),
        )
        with pytest.raises(HTTPException) as info:
            await get_auth_user(client, _USER_ID)
        assert info.value.status_code == 503

    async def test_transport_error_raises_503(self):
        client = _client_with_auth()
        client.auth.admin.get_user_by_id = AsyncMock(side_effect=httpx.ConnectError("down"))
        with pytest.raises(HTTPException) as info:
            await get_auth_user(client, _USER_ID)
        assert info.value.status_code == 503


class TestUpdateAuthUser:
    async def test_updates_successfully(self):
        client = _client_with_auth()
        client.auth.admin.update_user_by_id = AsyncMock(return_value=None)
        await update_auth_user(client, _USER_ID, {"email": "new@example.com"})
        client.auth.admin.update_user_by_id.assert_called_once_with(
            _USER_ID, {"email": "new@example.com"},
        )

    async def test_email_exists_raises_409(self):
        client = _client_with_auth()
        client.auth.admin.update_user_by_id = AsyncMock(
            side_effect=AuthApiError("exists", status=400, code="email_exists"),
        )
        with pytest.raises(HTTPException) as info:
            await update_auth_user(client, _USER_ID, {"email": "taken@example.com"})
        assert info.value.status_code == 409

    async def test_transport_error_raises_503(self):
        client = _client_with_auth()
        client.auth.admin.update_user_by_id = AsyncMock(side_effect=httpx.ConnectError("down"))
        with pytest.raises(HTTPException) as info:
            await update_auth_user(client, _USER_ID, {"email": "x@example.com"})
        assert info.value.status_code == 503


class TestUpdateAuthUserPassword:
    async def test_updates_successfully(self):
        client = _client_with_auth()
        client.auth.admin.update_user_by_id = AsyncMock(return_value=None)
        await update_auth_user_password(client, _USER_ID, new_password="newSecret123")
        client.auth.admin.update_user_by_id.assert_called_once_with(
            _USER_ID, {"password": "newSecret123"},
        )

    async def test_weak_password_error_raises_422(self):
        client = _client_with_auth()
        exc = AuthWeakPasswordError(message="too weak", status=422, reasons=["too short"])
        client.auth.admin.update_user_by_id = AsyncMock(side_effect=exc)
        with pytest.raises(HTTPException) as info:
            await update_auth_user_password(client, _USER_ID, new_password="weak")
        assert info.value.status_code == 422

    async def test_weak_password_api_error_raises_422(self):
        client = _client_with_auth()
        client.auth.admin.update_user_by_id = AsyncMock(
            side_effect=AuthApiError("weak", status=400, code="weak_password"),
        )
        with pytest.raises(HTTPException) as info:
            await update_auth_user_password(client, _USER_ID, new_password="weak")
        assert info.value.status_code == 422

    async def test_other_auth_api_error_uses_admin_mapping(self):
        client = _client_with_auth()
        client.auth.admin.update_user_by_id = AsyncMock(
            side_effect=AuthApiError("exists", status=400, code="email_exists"),
        )
        with pytest.raises(HTTPException) as info:
            await update_auth_user_password(client, _USER_ID, new_password="secret123")
        assert info.value.status_code == 409
