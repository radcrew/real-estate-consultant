"""Tests for POST /intake-sessions/{id}/answers/llm."""
from __future__ import annotations

from contextlib import ExitStack
from unittest.mock import AsyncMock, patch

from app.schemas.intake_sessions import IntakeSessionFirstQuestion

_SESSION_UUID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

# The turn pipeline lives in the service, so that is what these patch: the endpoint is a
# thin caller, and going through it keeps the wiring between the two covered.
_SERVICE = "app.services.intake_llm"

_SESSION_ROW = {
    "id": _SESSION_UUID,
    "status": "in_progress",
    "search_profile_id": None,
    "criteria": {},
}

_QUESTIONS = [
    {
        "key": "location",
        "title": "Location",
        "text": "Where?",
        "type": "location",
        "order_index": 0,
        "required": False,
        "options": None,
    },
    {
        "key": "property_type",
        "title": "Property Type",
        "text": "What type?",
        "type": "multiselect",
        "order_index": 1,
        "required": False,
        "options": None,
    },
]

_LLM_RESULT = {
    "extracted": {"location": "Austin"},
    "merged_criteria": {"location": "Austin"},
    "missing_fields": ["property_type"],
    "skipped_fields": [],
    "is_complete": False,
    "next_question": {"key": "property_type", "text": "What type?"},
}


def _enter_pipeline(stack, *, llm_result=None, next_question=None, parse=None):
    """Patch the service's collaborators, leaving its own logic under test."""
    patches = (
        patch(
            f"{_SERVICE}.get_intake_session_row",
            new_callable=AsyncMock,
            return_value=_SESSION_ROW,
        ),
        patch(
            f"{_SERVICE}.list_intake_questions",
            new_callable=AsyncMock,
            return_value=_QUESTIONS,
        ),
        patch(
            f"{_SERVICE}.parse_user_input",
            parse or AsyncMock(return_value=llm_result or _LLM_RESULT),
        ),
        patch(
            f"{_SERVICE}.save_intake_criteria",
            new_callable=AsyncMock,
            return_value=_SESSION_ROW,
        ),
        patch(f"{_SERVICE}.resolve_next_intake_question", return_value=next_question),
    )
    for item in patches:
        stack.enter_context(item)


class TestSubmitLlmAnswer:
    async def test_success_returns_response(self, client):
        next_q = IntakeSessionFirstQuestion(
            key="property_type",
            title="Property Type",
            text="What type of property?",
            type="multiselect",
        )
        with ExitStack() as stack:
            _enter_pipeline(stack, next_question=next_q)
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
        with ExitStack() as stack:
            _enter_pipeline(stack, llm_result=complete_result)
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


class TestAdmissionControl:
    async def test_exhausted_budget_returns_429_without_calling_the_model(
        self, client, monkeypatch
    ):
        """Wiring test: the endpoint is anonymous, so the limiter is the only gate.

        Asserting the provider was never reached is the part that matters — a 429 that
        still ran the model would protect nothing.
        """
        from app.core import intake_admission as module
        from app.core.intake_admission import IntakeAdmissionControl

        monkeypatch.setattr(
            module,
            "intake_admission",
            IntakeAdmissionControl(ip_per_minute=1, session_per_minute=1),
        )

        parse = AsyncMock(return_value=_LLM_RESULT)
        with ExitStack() as stack:
            _enter_pipeline(stack, parse=parse)
            first = await client.post(
                f"/api/v1/intake-sessions/{_SESSION_UUID}/answers/llm",
                json={"input": "warehouse in Austin"},
            )
            second = await client.post(
                f"/api/v1/intake-sessions/{_SESSION_UUID}/answers/llm",
                json={"input": "actually, Dallas"},
            )

        assert first.status_code == 200
        assert second.status_code == 429
        assert second.headers["retry-after"] == "60"
        assert parse.await_count == 1
