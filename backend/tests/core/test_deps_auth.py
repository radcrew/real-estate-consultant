"""Auth in ``app.core.deps``: Cognito bearer tokens and MCP API keys.

Identity comes from the token or key; a token's ``sub`` is mapped to the app user id
through ``cognito_identity_mapping``. Auth never reads ``public.profiles``.
Calls the dependencies directly so these run without building the FastAPI app.
"""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core import deps
from app.core.db_safe import SupabaseRequestError
from app.models.auth_user import AuthUser
from app.repositories.mcp_api_keys import ResolvedMcpApiKey

_SUB = "6f1c2a9e-0000-4000-8000-000000000001"
_SUPABASE_UUID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"


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
def mapping():
    """Unmapped by default: the sub is the user id. Each test starts with an empty cache."""
    deps._user_id_by_sub.clear()
    with patch.object(deps, "resolve_user_id", new_callable=AsyncMock) as mock:
        mock.side_effect = lambda _client, sub: sub
        yield mock
    deps._user_id_by_sub.clear()


@pytest.fixture(autouse=True)
def profile_row():
    """Auth must not read profiles; any call is a failure."""
    with patch.object(deps, "get_profile_row", new_callable=AsyncMock) as mock:
        yield mock


async def _current_user(*args):
    return await deps.get_current_user(*args, MagicMock())


async def _current_user_jwt(*args):
    return await deps.get_current_user_jwt(*args, MagicMock())


@pytest.mark.parametrize("dependency", [_current_user, _current_user_jwt])
class TestBearerAuth:
    async def test_valid_token_returns_the_token_user(self, dependency, verify, profile_row):
        user = await dependency(_request(), _bearer())
        assert user == AuthUser(id=_SUB, username="google_123")
        verify.assert_called_once_with("access-token")
        profile_row.assert_not_called()

    async def test_mapped_sub_becomes_the_supabase_uuid(self, dependency, verify, mapping):
        mapping.side_effect = None
        mapping.return_value = _SUPABASE_UUID
        user = await dependency(_request(), _bearer())
        assert user == AuthUser(id=_SUPABASE_UUID, username="google_123")
        assert mapping.call_args.args[1] == _SUB

    async def test_mapping_is_cached_per_sub(self, dependency, verify, mapping):
        mapping.side_effect = None
        mapping.return_value = _SUPABASE_UUID
        await dependency(_request(), _bearer())
        with patch.object(deps.time, "monotonic", return_value=time.monotonic() + 3600):
            await dependency(_request(), _bearer())
        mapping.assert_called_once()

    async def test_unmapped_sub_is_cached_briefly(self, dependency, verify, mapping):
        await dependency(_request(), _bearer())
        await dependency(_request(), _bearer())
        mapping.assert_called_once()

    async def test_mapping_row_added_later_is_seen_after_the_expiry(
        self, dependency, verify, mapping
    ):
        """A migrated user who signs in before their row exists must not stay unmapped."""
        assert (await dependency(_request(), _bearer())).id == _SUB
        mapping.side_effect = None
        mapping.return_value = _SUPABASE_UUID
        later = time.monotonic() + deps._UNMAPPED_TTL_SECONDS + 1
        with patch.object(deps.time, "monotonic", return_value=later):
            user = await dependency(_request(), _bearer())
        assert user.id == _SUPABASE_UUID

    async def test_expired_entries_are_pruned_once_the_cache_is_full(
        self, dependency, verify, mapping, monkeypatch
    ):
        monkeypatch.setattr(deps, "_CACHE_PRUNE_SIZE", 2)
        deps._user_id_by_sub["expired"] = ("expired", 0.0)
        deps._user_id_by_sub["mapped"] = (_SUPABASE_UUID, float("inf"))

        await dependency(_request(), _bearer())

        assert set(deps._user_id_by_sub) == {"mapped", _SUB}

    async def test_mapping_lookup_failure_is_503(self, dependency, verify, mapping):
        """Guessing the sub here would hide a migrated user's data, so fail instead."""
        mapping.side_effect = SupabaseRequestError("down")
        with pytest.raises(HTTPException) as info:
            await dependency(_request(), _bearer())
        assert info.value.status_code == 503

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

    async def test_key_user_is_the_key_owner(self, resolve, verify, profile_row, mapping):
        request = _request({"X-API-Key": "rad_abcdefghijklmnop"})
        user = await deps.get_current_user(request, None, MagicMock())
        assert user == AuthUser(id=_SUB)
        verify.assert_not_called()
        profile_row.assert_not_called()
        # The key already stores the app user id; no mapping lookup.
        mapping.assert_not_called()

    async def test_unknown_key_is_401(self, resolve):
        resolve.return_value = None
        request = _request({"X-API-Key": "rad_abcdefghijklmnop"})
        with pytest.raises(HTTPException) as info:
            await deps.get_current_user(request, None, MagicMock())
        assert info.value.status_code == 401
