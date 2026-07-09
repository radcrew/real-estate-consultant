import pytest
from fastapi import HTTPException

from app.repositories.listing_submissions import (
    create_listing_submission,
    list_listing_submissions,
    update_submission_status,
)
from tests.repositories.conftest import make_supabase_client

_SUBMISSION_ROW = {"id": "sub-1", "status": "pending", "address": "100 Main St"}


class TestCreateListingSubmission:
    async def test_returns_inserted_row(self):
        client = make_supabase_client([_SUBMISSION_ROW])
        result = await create_listing_submission(client, {"address": "100 Main St"})
        assert result == _SUBMISSION_ROW

    async def test_raises_502_on_empty_response(self):
        client = make_supabase_client([])
        with pytest.raises(HTTPException) as info:
            await create_listing_submission(client, {"address": "100 Main St"})
        assert info.value.status_code == 502


class TestListListingSubmissions:
    async def test_returns_all_rows_by_default(self):
        client = make_supabase_client([_SUBMISSION_ROW])
        result = await list_listing_submissions(client)
        assert result == [_SUBMISSION_ROW]

    async def test_filters_by_status_when_given(self):
        client = make_supabase_client([_SUBMISSION_ROW])
        await list_listing_submissions(client, status="pending")
        client.table.return_value.eq.assert_called_once_with("status", "pending")

    async def test_skips_status_filter_when_not_given(self):
        client = make_supabase_client([_SUBMISSION_ROW])
        await list_listing_submissions(client)
        client.table.return_value.eq.assert_not_called()


class TestUpdateSubmissionStatus:
    async def test_returns_updated_row(self):
        updated = {**_SUBMISSION_ROW, "status": "approved"}
        client = make_supabase_client([updated])
        result = await update_submission_status(client, "sub-1", "approved")
        assert result == updated

    async def test_returns_none_when_not_found(self):
        client = make_supabase_client([])
        result = await update_submission_status(client, "sub-1", "approved")
        assert result is None
