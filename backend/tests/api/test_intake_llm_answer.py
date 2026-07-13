"""Tests for POST /intake-sessions/{id}/answers/llm."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

_SESSION_UUID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

_SESSION_ROW = {
    "id": _SESSION_UUID,
    "status": "in_progress",
    "search_profile_id": None,
    "criteria": {},
}

_QUESTIONS = [
    {"key": "location", "title": "Location", "text": "Where?", "type": "location", "order_index": 0, "required": False, "options": None},
    {"key": "property_type", "title": "Property Type", "text": "What type?", "type": "multiselect", "order_index": 1, "required": False, "options": None},
]

_LLM_RESULT = {
    "extracted": {"location": "Austin"},
    "merged_criteria": {"location": "Austin"},
    "missing_fields": ["property_type"],
    "skipped_fields": [],
    "is_complete": False,
    "next_question": {"key": "property_type", "text": "What type?"},
}


class TestSubmitLlmAnswer:
    async def test_success_returns_response(self, client):
        from app.schemas.intake_sessions import IntakeSessionFirstQuestion
        next_q = IntakeSessionFirstQuestion(
            key="property_type",
            title="Property Type",
            text="What type of property?",
            type="multiselect",
        )
        with (
            patch("app.api.v1.endpoints.intake_sessions.answers.llm.get_intake_session_row", new_callable=AsyncMock, return_value=_SESSION_ROW),
            patch("app.api.v1.endpoints.intake_sessions.answers.llm.list_intake_questions", new_callable=AsyncMock, return_value=_QUESTIONS),
            patch("app.api.v1.endpoints.intake_sessions.answers.llm.parse_user_input", new_callable=AsyncMock, return_value=_LLM_RESULT),
            patch("app.api.v1.endpoints.intake_sessions.answers.llm.save_intake_criteria", new_callable=AsyncMock, return_value=_SESSION_ROW),
            patch("app.api.v1.endpoints.intake_sessions.answers.llm.resolve_next_intake_question", return_value=next_q),
        ):
            r = await client.post(
                f"/api/v1/intake-sessions/{_SESSION_UUID}/answers/llm",
                json={"input": "I need a warehouse in Austin"},
            )
        assert r.status_code == 200
        body = r.json()
        assert body["extracted"] == {"location": "Austin"}
        assert body["missing_fields"] == ["property_type"]
        assert body["is_complete"] is False
        assert body["next_question"]["key"] == "property_type"

    async def test_complete_session_is_marked(self, client):
        complete_result = {**_LLM_RESULT, "missing_fields": [], "is_complete": True}
        with (
            patch("app.api.v1.endpoints.intake_sessions.answers.llm.get_intake_session_row", new_callable=AsyncMock, return_value=_SESSION_ROW),
            patch("app.api.v1.endpoints.intake_sessions.answers.llm.list_intake_questions", new_callable=AsyncMock, return_value=_QUESTIONS),
            patch("app.api.v1.endpoints.intake_sessions.answers.llm.parse_user_input", new_callable=AsyncMock, return_value=complete_result),
            patch("app.api.v1.endpoints.intake_sessions.answers.llm.save_intake_criteria", new_callable=AsyncMock, return_value=_SESSION_ROW),
            patch("app.api.v1.endpoints.intake_sessions.answers.llm.resolve_next_intake_question", return_value=None),
        ):
            r = await client.post(
                f"/api/v1/intake-sessions/{_SESSION_UUID}/answers/llm",
                json={"input": "office in Dallas under 1M"},
            )
        assert r.status_code == 200
        assert r.json()["is_complete"] is True
        assert r.json()["next_question"] is None

    async def test_missing_input_returns_422(self, client):
        r = await client.post(
            f"/api/v1/intake-sessions/{_SESSION_UUID}/answers/llm",
            json={},
        )
        assert r.status_code == 422
