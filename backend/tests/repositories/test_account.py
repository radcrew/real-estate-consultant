from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastapi import HTTPException

from app.models.auth_user import AuthUser
from app.repositories.account import (
    get_auth_user,
    update_auth_user,
)
from supabase import AuthApiError

_USER_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"


def _client_with_auth() -> MagicMock:
    client = MagicMock()
    client.auth = MagicMock()
    client.auth.admin = MagicMock()
    return client


class TestGetAuthUser:
    async def test_returns_user(self):
        client = _client_with_auth()
        fake_user = MagicMock(id=_USER_ID, email="u@example.com", phone=None)
        client.auth.admin.get_user_by_id = AsyncMock(return_value=MagicMock(user=fake_user))
        result = await get_auth_user(client, _USER_ID)
        assert result == AuthUser(id=_USER_ID, email="u@example.com", phone=None)

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
