"""Tests for intake-sessions endpoints."""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_SESSION_UUID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
_PROFILE_UUID = "b2c3d4e5-f6a7-8901-bcde-f12345678901"

_SESSION_ROW = {
    "id": _SESSION_UUID,
    "status": "in_progress",
    "search_profile_id": None,
    "criteria": {},
}

_QUESTIONS = [
    {"key": "location", "title": "Location", "text": "Where?", "type": "location", "order_index": 0, "required": False, "options": None},
    {"key": "property_type", "title": "Property Type", "text": "What type?", "type": "multiselect", "order_index": 1, "required": False, "options": ["Industrial", "Office"]},
]


def _make_session(criteria=None):
    from app.models.intake_sessions import IntakeSession
    return IntakeSession(id=uuid.UUID(_SESSION_UUID), status="in_progress", criteria=criteria or {})


class TestCreateIntakeSession:
    async def test_guided_mode_returns_first_question(self, client):
        session = _make_session()
        with (
            patch("app.api.v1.endpoints.intake_sessions.sessions.create_intake_session_row", new_callable=AsyncMock, return_value=session),
            patch("app.api.v1.endpoints.intake_sessions.sessions.list_intake_questions", new_callable=AsyncMock, return_value=_QUESTIONS),
        ):
            r = await client.post("/api/v1/intake-sessions/")
        assert r.status_code == 201
        body = r.json()
        assert body["mode"] == "guided"
        assert body["first_question"]["key"] == "location"
        assert body["total_questions"] == 2

    async def test_llm_mode_returns_opening_message(self, client):
        session = _make_session()
        with (
            patch("app.api.v1.endpoints.intake_sessions.sessions.create_intake_session_row", new_callable=AsyncMock, return_value=session),
            patch("app.api.v1.endpoints.intake_sessions.sessions.list_intake_questions", new_callable=AsyncMock, return_value=_QUESTIONS),
            patch("app.api.v1.endpoints.intake_sessions.sessions.generate_opening_question", new_callable=AsyncMock, return_value="Tell me where you're looking?"),
        ):
            r = await client.post("/api/v1/intake-sessions/?mode=llm")
        assert r.status_code == 201
        body = r.json()
        assert body["mode"] == "llm"
        assert body["next_question"]["key"] == "location"

    async def test_no_questions_returns_502(self, client):
        session = _make_session()
        with (
            patch("app.api.v1.endpoints.intake_sessions.sessions.create_intake_session_row", new_callable=AsyncMock, return_value=session),
            patch("app.api.v1.endpoints.intake_sessions.sessions.list_intake_questions", new_callable=AsyncMock, return_value=[]),
        ):
            r = await client.post("/api/v1/intake-sessions/")
        assert r.status_code == 502

    async def test_llm_mode_falls_back_on_llm_error(self, client):
        from fastapi import HTTPException
        session = _make_session()
        with (
            patch("app.api.v1.endpoints.intake_sessions.sessions.create_intake_session_row", new_callable=AsyncMock, return_value=session),
            patch("app.api.v1.endpoints.intake_sessions.sessions.list_intake_questions", new_callable=AsyncMock, return_value=_QUESTIONS),
            patch("app.api.v1.endpoints.intake_sessions.sessions.generate_opening_question", new_callable=AsyncMock, side_effect=HTTPException(status_code=502, detail="LLM down")),
        ):
            r = await client.post("/api/v1/intake-sessions/?mode=llm")
        assert r.status_code == 201
        assert r.json()["next_question"]["text"] == "Where?"


class TestGetIntakeSession:
    async def test_returns_session_with_history(self, client):
        session = _make_session(criteria={"location": "Austin"})
        with (
            patch("app.api.v1.endpoints.intake_sessions.sessions.get_intake_session_row", new_callable=AsyncMock, return_value={**_SESSION_ROW, "criteria": {"location": "Austin"}}),
            patch("app.api.v1.endpoints.intake_sessions.sessions.ensure_search_profile_access", new_callable=AsyncMock),
            patch("app.api.v1.endpoints.intake_sessions.sessions.parse_intake_session", return_value=session),
            patch("app.api.v1.endpoints.intake_sessions.sessions.list_intake_questions", new_callable=AsyncMock, return_value=_QUESTIONS),
        ):
            r = await client.get(f"/api/v1/intake-sessions/{_SESSION_UUID}")
        assert r.status_code == 200
        body = r.json()
        assert body["total_questions"] == 2
        assert len(body["question_history"]) == 1
        assert body["question_history"][0]["key"] == "location"
        assert body["next_question"]["key"] == "property_type"


class TestCompleteIntakeSession:
    async def test_success_returns_completed_session(self, client):
        session = _make_session()
        updated_row = {**_SESSION_ROW, "status": "complete", "search_profile_id": _PROFILE_UUID}
        with (
            patch("app.api.v1.endpoints.intake_sessions.actions.get_intake_session_row", new_callable=AsyncMock, return_value=_SESSION_ROW),
            patch("app.api.v1.endpoints.intake_sessions.actions.ensure_search_profile_access", new_callable=AsyncMock, return_value=uuid.UUID(_PROFILE_UUID)),
            patch("app.api.v1.endpoints.intake_sessions.actions.update_intake_session_completed", new_callable=AsyncMock, return_value=updated_row),
            patch("app.api.v1.endpoints.intake_sessions.actions.parse_intake_session", return_value=session),
        ):
            r = await client.post(f"/api/v1/intake-sessions/{_SESSION_UUID}/complete")
        assert r.status_code == 200

    async def test_creates_profile_when_none(self, client):
        session = _make_session()
        updated_row = {**_SESSION_ROW, "status": "complete"}
        with (
            patch("app.api.v1.endpoints.intake_sessions.actions.get_intake_session_row", new_callable=AsyncMock, return_value=_SESSION_ROW),
            patch("app.api.v1.endpoints.intake_sessions.actions.ensure_search_profile_access", new_callable=AsyncMock, return_value=None),
            patch("app.api.v1.endpoints.intake_sessions.actions.create_search_profile", new_callable=AsyncMock, return_value=uuid.UUID(_PROFILE_UUID)),
            patch("app.api.v1.endpoints.intake_sessions.actions.update_intake_session_completed", new_callable=AsyncMock, return_value=updated_row),
            patch("app.api.v1.endpoints.intake_sessions.actions.parse_intake_session", return_value=session),
        ):
            r = await client.post(f"/api/v1/intake-sessions/{_SESSION_UUID}/complete")
        assert r.status_code == 200


class TestSubmitGuidedAnswer:
    async def test_success_returns_next_question(self, client):
        session = _make_session(criteria={"location": "Austin"})
        with (
            patch("app.api.v1.endpoints.intake_sessions.answers.guided.get_intake_session_row", new_callable=AsyncMock, return_value=_SESSION_ROW),
            patch("app.api.v1.endpoints.intake_sessions.answers.guided.list_intake_questions", new_callable=AsyncMock, return_value=_QUESTIONS),
            patch("app.api.v1.endpoints.intake_sessions.answers.guided.append_intake_criteria_answer", return_value={"location": "Austin"}),
            patch("app.api.v1.endpoints.intake_sessions.answers.guided.order_for_question_key", return_value=0),
            patch("app.api.v1.endpoints.intake_sessions.answers.guided.next_question_row_after_order", return_value=_QUESTIONS[1]),
            patch("app.api.v1.endpoints.intake_sessions.answers.guided.save_intake_criteria", new_callable=AsyncMock, return_value=_SESSION_ROW),
            patch("app.api.v1.endpoints.intake_sessions.answers.guided.parse_intake_session", return_value=session),
        ):
            r = await client.patch(
                f"/api/v1/intake-sessions/{_SESSION_UUID}/answers/guided",
                json={"key": "location", "answers": "Austin"},
            )
        assert r.status_code == 200
        body = r.json()
        assert body["next_question"]["key"] == "property_type"

    async def test_unknown_key_returns_400(self, client):
        with (
            patch("app.api.v1.endpoints.intake_sessions.answers.guided.get_intake_session_row", new_callable=AsyncMock, return_value=_SESSION_ROW),
            patch("app.api.v1.endpoints.intake_sessions.answers.guided.list_intake_questions", new_callable=AsyncMock, return_value=_QUESTIONS),
            patch("app.api.v1.endpoints.intake_sessions.answers.guided.append_intake_criteria_answer", return_value={}),
            patch("app.api.v1.endpoints.intake_sessions.answers.guided.order_for_question_key", return_value=None),
        ):
            r = await client.patch(
                f"/api/v1/intake-sessions/{_SESSION_UUID}/answers/guided",
                json={"key": "unknown_key", "answers": "value"},
            )
        assert r.status_code == 400
