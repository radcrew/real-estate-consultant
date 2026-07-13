from app.repositories.profiles import (
    get_profile_row,
    set_profile_avatar_url,
    upsert_profile_patch,
)
from app.schemas.account import AccountProfileUpdate
from tests.repositories.conftest import make_supabase_client

_USER_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
_PROFILE_ROW = {"id": _USER_ID, "email": "u@example.com", "first_name": "Alice"}


class TestGetProfileRow:
    async def test_returns_row_when_found(self):
        client = make_supabase_client([_PROFILE_ROW])
        result = await get_profile_row(client, _USER_ID)
        assert result == _PROFILE_ROW

    async def test_returns_none_when_not_found(self):
        client = make_supabase_client([])
        result = await get_profile_row(client, _USER_ID)
        assert result is None


class TestUpsertProfilePatch:
    async def test_no_fields_set_does_nothing(self):
        client = make_supabase_client([_PROFILE_ROW])
        body = AccountProfileUpdate()
        await upsert_profile_patch(client, _USER_ID, body)
        client.table.assert_not_called()

    async def test_inserts_when_no_existing_profile(self):
        client = make_supabase_client([])
        body = AccountProfileUpdate(first_name="Alice")
        await upsert_profile_patch(client, _USER_ID, body)
        client.table.return_value.insert.assert_called_once_with(
            {"id": _USER_ID, "first_name": "Alice"},
        )

    async def test_updates_when_profile_exists(self):
        client = make_supabase_client([_PROFILE_ROW])
        body = AccountProfileUpdate(first_name="Alice")
        await upsert_profile_patch(client, _USER_ID, body)
        client.table.return_value.update.assert_called_once_with({"first_name": "Alice"})

    async def test_ignores_fields_outside_patch_columns(self):
        client = make_supabase_client([])
        body = AccountProfileUpdate(first_name="Alice")
        await upsert_profile_patch(client, _USER_ID, body)
        payload = client.table.return_value.insert.call_args[0][0]
        assert "phone" not in payload


class TestSetProfileAvatarUrl:
    async def test_inserts_when_no_existing_profile(self):
        client = make_supabase_client([])
        await set_profile_avatar_url(client, _USER_ID, "https://example.com/a.png")
        client.table.return_value.insert.assert_called_once_with(
            {"id": _USER_ID, "avatar_url": "https://example.com/a.png"},
        )

    async def test_updates_when_profile_exists(self):
        client = make_supabase_client([_PROFILE_ROW])
        await set_profile_avatar_url(client, _USER_ID, "https://example.com/a.png")
        client.table.return_value.update.assert_called_once_with(
            {"avatar_url": "https://example.com/a.png"},
        )
