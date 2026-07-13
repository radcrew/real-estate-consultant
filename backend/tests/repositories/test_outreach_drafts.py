import pytest
from fastapi import HTTPException

from app.repositories.outreach_drafts import (
    get_latest_outreach_draft_for_property,
    get_outreach_draft_for_user,
    insert_outreach_draft,
    update_outreach_draft_email,
)
from tests.repositories.conftest import make_supabase_client

_USER_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
_PROPERTY_ID = "b2c3d4e5-f6a7-8901-bcde-f23456789012"
_DRAFT_ID = "c3d4e5f6-a7b8-9012-cdef-345678901234"
_DRAFT_ROW = {
    "id": _DRAFT_ID,
    "property_id": _PROPERTY_ID,
    "user_id": _USER_ID,
    "draft_email": "Dear Bob,",
    "created_at": "2026-01-01T00:00:00Z",
}


class TestInsertOutreachDraft:
    async def test_returns_inserted_row(self):
        client = make_supabase_client([_DRAFT_ROW])
        result = await insert_outreach_draft(
            client,
            user_id=_USER_ID,
            property_id=_PROPERTY_ID,
            draft_email="Dear Bob,",
        )
        assert result == _DRAFT_ROW

    async def test_raises_502_on_empty_response(self):
        client = make_supabase_client([])
        with pytest.raises(HTTPException) as info:
            await insert_outreach_draft(
                client,
                user_id=_USER_ID,
                property_id=_PROPERTY_ID,
                draft_email="Dear Bob,",
            )
        assert info.value.status_code == 502


class TestGetOutreachDraftForUser:
    async def test_returns_row_when_found(self):
        client = make_supabase_client([_DRAFT_ROW])
        result = await get_outreach_draft_for_user(client, draft_id=_DRAFT_ID, user_id=_USER_ID)
        assert result == _DRAFT_ROW

    async def test_returns_none_when_not_found(self):
        client = make_supabase_client([])
        result = await get_outreach_draft_for_user(client, draft_id=_DRAFT_ID, user_id=_USER_ID)
        assert result is None


class TestGetLatestOutreachDraftForProperty:
    async def test_returns_most_recent_row(self):
        client = make_supabase_client([_DRAFT_ROW])
        result = await get_latest_outreach_draft_for_property(
            client,
            user_id=_USER_ID,
            property_id=_PROPERTY_ID,
        )
        assert result == _DRAFT_ROW

    async def test_returns_none_when_no_draft_exists(self):
        client = make_supabase_client([])
        result = await get_latest_outreach_draft_for_property(
            client,
            user_id=_USER_ID,
            property_id=_PROPERTY_ID,
        )
        assert result is None


class TestUpdateOutreachDraftEmail:
    async def test_returns_updated_row(self):
        updated = {**_DRAFT_ROW, "draft_email": "New text"}
        client = make_supabase_client([updated])
        result = await update_outreach_draft_email(
            client,
            draft_id=_DRAFT_ID,
            user_id=_USER_ID,
            draft_email="New text",
        )
        assert result == updated

    async def test_returns_none_when_no_row_updated(self):
        client = make_supabase_client([])
        result = await update_outreach_draft_email(
            client,
            draft_id=_DRAFT_ID,
            user_id=_USER_ID,
            draft_email="New text",
        )
        assert result is None
