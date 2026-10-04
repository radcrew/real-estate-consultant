import pytest

from app.core.db_safe import SupabaseRequestError
from app.repositories.identity_mapping import resolve_user_id
from tests.repositories.conftest import make_supabase_client

_SUB = "6f1c2a9e-0000-4000-8000-000000000001"
_UUID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"


class TestResolveUserId:
    async def test_mapped_sub_returns_the_supabase_uuid(self):
        client = make_supabase_client([{"uuid": _UUID}])
        assert await resolve_user_id(client, _SUB) == _UUID

    async def test_unmapped_sub_is_its_own_user_id(self):
        client = make_supabase_client([])
        assert await resolve_user_id(client, _SUB) == _SUB

    async def test_looks_up_by_sub_in_the_mapping_table(self):
        client = make_supabase_client([])
        await resolve_user_id(client, _SUB)
        client.table.assert_called_once_with("cognito_identity_mapping")
        client.table.return_value.eq.assert_called_once_with("sub", _SUB)

    async def test_database_error_propagates(self):
        """Falling back to the sub here would silently hide a migrated user's data."""
        client = make_supabase_client([])
        client.table.return_value.execute.side_effect = SupabaseRequestError("down")
        with pytest.raises(SupabaseRequestError):
            await resolve_user_id(client, _SUB)
