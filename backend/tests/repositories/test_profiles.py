from app.repositories.profiles import (
    ensure_profile_row,
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

    async def test_upserts_only_the_patched_columns_in_one_call(self):
        client = make_supabase_client([])
        body = AccountProfileUpdate(first_name="Alice")
        await upsert_profile_patch(client, _USER_ID, body)
        client.table.return_value.upsert.assert_called_once_with(
            {"id": _USER_ID, "first_name": "Alice"}, on_conflict="id"
        )
        client.table.return_value.select.assert_not_called()


class TestEnsureProfileRow:
    async def test_inserts_a_missing_row(self):
        client = make_supabase_client([])
        await ensure_profile_row(
            client, _USER_ID, email="u@example.com", first_name="Alice", last_name=None
        )
        client.table.return_value.upsert.assert_called_once_with(
            {"id": _USER_ID, "email": "u@example.com", "first_name": "Alice"},
            on_conflict="id",
            ignore_duplicates=True,
        )

    async def test_fills_only_the_empty_fields_of_an_existing_row(self):
        """Rows created before sign-in wrote them can lack an email or names."""
        client = make_supabase_client(
            [{"id": _USER_ID, "email": None, "first_name": "Edited", "last_name": ""}]
        )
        await ensure_profile_row(
            client, _USER_ID, email="u@example.com", first_name="Alice", last_name="Smith"
        )
        client.table.return_value.update.assert_called_once_with(
            {"email": "u@example.com", "last_name": "Smith"}
        )
        client.table.return_value.upsert.assert_not_called()

    async def test_complete_row_is_not_written(self):
        client = make_supabase_client([_PROFILE_ROW | {"last_name": "Smith"}])
        await ensure_profile_row(
            client, _USER_ID, email="new@example.com", first_name="Bob", last_name="Jones"
        )
        client.table.return_value.update.assert_not_called()
        client.table.return_value.upsert.assert_not_called()


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
