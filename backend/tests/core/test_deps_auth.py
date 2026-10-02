"""Auth in ``app.core.deps``: Cognito bearer tokens and MCP API keys.

Identity comes from the token or key alone; auth never reads ``public.profiles``.
Calls the dependencies directly so these run without building the FastAPI app.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core import deps
from app.models.auth_user import AuthUser
from app.repositories.mcp_api_keys import ResolvedMcpApiKey

_SUB = "6f1c2a9e-0000-4000-8000-000000000001"


def _request(headers: dict[str, str] | None = None) -> MagicMock:
    request = MagicMock()
    request.headers = headers or {}
    request.method = "GET"
    return request


def _bearer(token: str = "access-token") -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


@pytest.fixture
def verify():
    claims = {"sub": _SUB, "username": "google_123"}
    with patch.object(deps, "verify_access_token", return_value=claims) as mock:
        yield mock


@pytest.fixture(autouse=True)
def profile_row():
    """Auth must not read profiles; any call is a failure."""
    with patch.object(deps, "get_profile_row", new_callable=AsyncMock) as mock:
        yield mock


async def _current_user(*args):
    return await deps.get_current_user(*args, MagicMock())


async def _current_user_jwt(*args):
    return await deps.get_current_user_jwt(*args)


@pytest.mark.parametrize("dependency", [_current_user, _current_user_jwt])
class TestBearerAuth:
    async def test_valid_token_returns_the_token_user(self, dependency, verify, profile_row):
        user = await dependency(_request(), _bearer())
        assert user == AuthUser(id=_SUB, username="google_123")
        verify.assert_called_once_with("access-token")
        profile_row.assert_not_called()

    async def test_invalid_token_is_401(self, dependency, verify):
        verify.side_effect = jwt.ExpiredSignatureError("Signature has expired")
        with pytest.raises(HTTPException) as info:
            await dependency(_request(), _bearer())
        assert info.value.status_code == 401

    async def test_unreachable_jwks_is_503_not_401(self, dependency, verify):
        """A Cognito outage must not look like a bad token, or clients sign users out."""
        verify.side_effect = jwt.PyJWKClientConnectionError("timed out")
        with pytest.raises(HTTPException) as info:
            await dependency(_request(), _bearer())
        assert info.value.status_code == 503

    async def test_missing_bearer_is_401(self, dependency, verify):
        with pytest.raises(HTTPException) as info:
            await dependency(_request(), None)
        assert info.value.status_code == 401
        verify.assert_not_called()


class TestApiKeyAuth:
    @pytest.fixture
    def resolve(self):
        resolved = ResolvedMcpApiKey(
            user_id=UUID(_SUB), key_id=uuid4(), key_prefix="rad_abcdefgh", scopes=["*"]
        )
        with patch.object(
            deps, "resolve_mcp_api_key", new_callable=AsyncMock, return_value=resolved
        ) as mock:
            yield mock

    async def test_key_user_is_the_key_owner(self, resolve, verify, profile_row):
        request = _request({"X-API-Key": "rad_abcdefghijklmnop"})
        user = await deps.get_current_user(request, None, MagicMock())
        assert user == AuthUser(id=_SUB)
        verify.assert_not_called()
        profile_row.assert_not_called()

    async def test_unknown_key_is_401(self, resolve):
        resolve.return_value = None
        request = _request({"X-API-Key": "rad_abcdefghijklmnop"})
        with pytest.raises(HTTPException) as info:
            await deps.get_current_user(request, None, MagicMock())
        assert info.value.status_code == 401
