import pytest
from fastapi import HTTPException

from app.repositories.intake_sessions import (
    append_intake_criteria_answer,
    create_intake_session_row,
    get_intake_session_row,
    get_profile_session_row,
    parse_intake_session,
    save_intake_criteria,
    strip_intake_session_row,
    update_intake_session_completed,
)
from tests.repositories.conftest import make_supabase_client

_SESSION_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
_PROFILE_ID = "b2c3d4e5-f6a7-8901-bcde-f23456789012"
_SESSION_ROW = {
    "id": _SESSION_ID,
    "status": "in_progress",
    "created_at": "2026-01-01T00:00:00Z",
    "search_profile_id": None,
    "criteria": {},
}


class TestStripIntakeSessionRow:
    def test_removes_embedded_relation_keys(self):
        row = {**_SESSION_ROW, "search_profiles": {"id": _PROFILE_ID}}
        result = strip_intake_session_row(row)
        assert "search_profiles" not in result
        assert result["id"] == _SESSION_ID

    def test_removes_extra_embedded_keys_when_given(self):
        row = {**_SESSION_ROW, "questions": [{"key": "price"}]}
        result = strip_intake_session_row(row, extra_embedded_keys=frozenset({"questions"}))
        assert "questions" not in result


class TestParseIntakeSession:
    def test_parses_row_into_model(self):
        session = parse_intake_session(_SESSION_ROW)
        assert str(session.id) == _SESSION_ID
        assert session.status == "in_progress"


class TestAppendIntakeCriteriaAnswer:
    def test_applies_answer_to_empty_criteria(self):
        result = append_intake_criteria_answer(None, "price", {"min": 1000, "max": 2000})
        assert result == {"price": {"min": 1000, "max": 2000}}

    def test_preserves_existing_criteria(self):
        result = append_intake_criteria_answer({"location": "Austin"}, "price", 1000)
        assert result == {"location": "Austin", "price": 1000}

    def test_strips_question_key(self):
        result = append_intake_criteria_answer({}, "  price  ", 1000)
        assert result == {"price": 1000}


class TestGetIntakeSessionRow:
    async def test_returns_row_when_found(self):
        client = make_supabase_client([_SESSION_ROW])
        result = await get_intake_session_row(client, _SESSION_ID)
        assert result == _SESSION_ROW

    async def test_raises_404_when_not_found(self):
        client = make_supabase_client([])
        with pytest.raises(HTTPException) as info:
            await get_intake_session_row(client, _SESSION_ID)
        assert info.value.status_code == 404


class TestGetProfileSessionRow:
    async def test_returns_most_recent_session(self):
        client = make_supabase_client([_SESSION_ROW])
        result = await get_profile_session_row(client, _PROFILE_ID)
        assert result == _SESSION_ROW

    async def test_raises_404_when_no_session_for_profile(self):
        client = make_supabase_client([])
        with pytest.raises(HTTPException) as info:
            await get_profile_session_row(client, _PROFILE_ID)
        assert info.value.status_code == 404


class TestCreateIntakeSessionRow:
    async def test_returns_parsed_session(self):
        client = make_supabase_client([_SESSION_ROW])
        result = await create_intake_session_row(client)
        assert str(result.id) == _SESSION_ID

    async def test_inserts_empty_criteria_and_no_profile(self):
        client = make_supabase_client([_SESSION_ROW])
        await create_intake_session_row(client)
        client.table.return_value.insert.assert_called_once_with(
            {"search_profile_id": None, "criteria": {}},
        )


class TestSaveIntakeCriteria:
    async def test_returns_updated_row(self):
        updated = {**_SESSION_ROW, "criteria": {"price": 1000}, "status": "in_progress"}
        client = make_supabase_client([updated])
        result = await save_intake_criteria(client, _SESSION_ID, {"price": 1000})
        assert result == updated

    async def test_raises_502_on_unexpected_response(self):
        client = make_supabase_client([])
        with pytest.raises(HTTPException) as info:
            await save_intake_criteria(client, _SESSION_ID, {"price": 1000})
        assert info.value.status_code == 502


class TestUpdateIntakeSessionCompleted:
    async def test_returns_completed_row(self):
        completed = {**_SESSION_ROW, "status": "completed", "search_profile_id": _PROFILE_ID}
        client = make_supabase_client([completed])
        result = await update_intake_session_completed(client, _SESSION_ID, _PROFILE_ID)
        assert result == completed

    async def test_raises_502_on_unexpected_response(self):
        client = make_supabase_client([])
        with pytest.raises(HTTPException) as info:
            await update_intake_session_completed(client, _SESSION_ID, _PROFILE_ID)
        assert info.value.status_code == 502
