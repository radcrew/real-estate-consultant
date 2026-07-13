import pytest
from fastapi import HTTPException

from app.repositories.search_profiles import create_search_profile, ensure_search_profile_access
from tests.repositories.conftest import make_supabase_client

_USER_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
_PROFILE_ID = "b2c3d4e5-f6a7-8901-bcde-f23456789012"


class TestEnsureSearchProfileAccess:
    async def test_returns_none_when_profile_id_is_none(self):
        client = make_supabase_client(None)
        result = await ensure_search_profile_access(client, None, _USER_ID)
        assert result is None
        client.table.assert_not_called()

    async def test_returns_profile_id_when_owned(self):
        client = make_supabase_client([{"id": _PROFILE_ID}])
        result = await ensure_search_profile_access(client, _PROFILE_ID, _USER_ID)
        assert result == _PROFILE_ID

    async def test_raises_404_when_not_owned(self):
        client = make_supabase_client([])
        with pytest.raises(HTTPException) as info:
            await ensure_search_profile_access(client, _PROFILE_ID, _USER_ID)
        assert info.value.status_code == 404


class TestCreateSearchProfile:
    async def test_returns_new_profile_id(self):
        client = make_supabase_client([{"id": _PROFILE_ID}])
        result = await create_search_profile(client, _USER_ID)
        assert result == _PROFILE_ID

    async def test_raises_502_when_id_missing(self):
        client = make_supabase_client([{"user_id": _USER_ID}])
        with pytest.raises(HTTPException) as info:
            await create_search_profile(client, _USER_ID)
        assert info.value.status_code == 502
