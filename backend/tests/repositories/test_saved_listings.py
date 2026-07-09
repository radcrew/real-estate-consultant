from app.repositories.saved_listings import (
    add_saved_listing,
    list_saved_property_ids,
    remove_saved_listing,
)
from tests.repositories.conftest import make_supabase_client

_USER_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
_PROPERTY_ID = "b2c3d4e5-f6a7-8901-bcde-f23456789012"


class TestListSavedPropertyIds:
    async def test_returns_property_ids(self):
        client = make_supabase_client([{"property_id": "p1"}, {"property_id": "p2"}])
        result = await list_saved_property_ids(client, _USER_ID)
        assert result == ["p1", "p2"]

    async def test_returns_empty_list_when_none_saved(self):
        client = make_supabase_client([])
        result = await list_saved_property_ids(client, _USER_ID)
        assert result == []

    async def test_skips_malformed_rows(self):
        client = make_supabase_client([{"property_id": "p1"}, {"property_id": None}, {}])
        result = await list_saved_property_ids(client, _USER_ID)
        assert result == ["p1"]


class TestAddSavedListing:
    async def test_upserts_user_and_property_id(self):
        client = make_supabase_client(None)
        await add_saved_listing(client, _USER_ID, _PROPERTY_ID)
        client.table.return_value.upsert.assert_called_once_with(
            {"user_id": _USER_ID, "property_id": _PROPERTY_ID},
        )


class TestRemoveSavedListing:
    async def test_deletes_by_user_and_property_id(self):
        client = make_supabase_client(None)
        await remove_saved_listing(client, _USER_ID, _PROPERTY_ID)
        table = client.table.return_value
        table.delete.assert_called_once_with()
        table.eq.assert_any_call("user_id", _USER_ID)
        table.eq.assert_any_call("property_id", _PROPERTY_ID)
