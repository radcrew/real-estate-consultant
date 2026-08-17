"""Tests for the extracted intake-turn pipeline.

These cover the service directly rather than through the endpoint, because the queued
worker will call it the same way — anything only asserted via HTTP would stop being
covered the moment the worker becomes the caller.
"""
from __future__ import annotations

from contextlib import ExitStack
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.clients.bedrock_guardrail import GuardrailOutcome
from app.schemas.intake_sessions import IntakeSessionFirstQuestion
from app.services.intake_llm import (
    question_titles_for,
    run_llm_intake_turn,
    screen_generated_question,
)

_SERVICE = "app.services.intake_llm"
_SESSION_ID = uuid4()

_QUESTIONS = [
    {
        "key": "location",
        "title": "Location",
        "text": "Where?",
        "type": "location",
        "order_index": 0,
        "required": True,
        "options": None,
    },
    {
        "key": "property_type",
        "title": None,
        "text": "What type?",
        "type": "multiselect",
        "order_index": 1,
        "required": False,
        "options": None,
    },
]

_LLM_RESULT = {
    "extracted": {"location": "Austin"},
    "merged_criteria": {"location": "Austin", "_skipped_fields": ["budget"]},
    "missing_fields": ["property_type"],
    "skipped_fields": ["budget"],
    "is_complete": False,
    "next_question": {"key": "property_type", "text": "What type?"},
}


def _enter(stack, *, session_row=None, llm_result=None, save=None, parse=None):
    save_mock = save or AsyncMock(return_value={})
    parse_mock = parse or AsyncMock(return_value=llm_result or _LLM_RESULT)
    for item in (
        patch(
            f"{_SERVICE}.get_intake_session_row",
            new_callable=AsyncMock,
            return_value=session_row if session_row is not None else {"criteria": {}},
        ),
        patch(
            f"{_SERVICE}.list_intake_questions",
            new_callable=AsyncMock,
            return_value=_QUESTIONS,
        ),
        patch(f"{_SERVICE}.parse_user_input", parse_mock),
        patch(f"{_SERVICE}.save_intake_criteria", save_mock),
        patch(f"{_SERVICE}.resolve_next_intake_question", return_value=None),
    ):
        stack.enter_context(item)
    return parse_mock, save_mock


class TestScreenGeneratedQuestion:
    async def test_off_by_default(self):
        """It doubles the per-turn guardrail cost for template-driven text."""
        question = IntakeSessionFirstQuestion(key="k", title="T", text="What size?", type="text")
        guardrail = MagicMock()
        with ExitStack() as stack:
            stack.enter_context(patch(f"{_SERVICE}.bedrock_guardrail", guardrail))
            cfg = stack.enter_context(patch(f"{_SERVICE}.settings"))
            cfg.bedrock_guardrail_screen_output = False
            assert await screen_generated_question(question) is question
        guardrail.screen.assert_not_called()

    async def test_masked_text_replaces_the_question(self):
        question = IntakeSessionFirstQuestion(
            key="k", title="T", text="Near 1 Main St?", type="text"
        )
        guardrail = MagicMock()
        guardrail.screen = AsyncMock(
            return_value=GuardrailOutcome(text="Near {PII}?", blocked=False)
        )
        with ExitStack() as stack:
            stack.enter_context(patch(f"{_SERVICE}.bedrock_guardrail", guardrail))
            cfg = stack.enter_context(patch(f"{_SERVICE}.settings"))
            cfg.bedrock_guardrail_screen_output = True
            screened = await screen_generated_question(question)
        assert screened is not None
        assert screened.text == "Near {PII}?"

    async def test_a_guardrail_outage_does_not_fail_the_turn(self):
        """The parse already succeeded. Propagating would requeue the turn on the worker
        — re-paying for the model call — or discard the message inline, to protect one
        line of template-driven prose."""
        question = IntakeSessionFirstQuestion(key="k", title="T", text="What size?", type="text")
        guardrail = MagicMock()
        guardrail.screen = AsyncMock(
            side_effect=HTTPException(status_code=503, detail="guardrail down")
        )
        with ExitStack() as stack:
            stack.enter_context(patch(f"{_SERVICE}.bedrock_guardrail", guardrail))
            cfg = stack.enter_context(patch(f"{_SERVICE}.settings"))
            cfg.bedrock_guardrail_screen_output = True
            screened = await screen_generated_question(question)
        assert screened is not None
        # Screening was asked for and could not run, so unscreened text is not shown.
        assert screened.text == ""

    async def test_a_blocked_question_falls_back_to_no_text(self):
        """The client already handles this by showing the question row's own wording."""
        question = IntakeSessionFirstQuestion(key="k", title="T", text="bad", type="text")
        guardrail = MagicMock()
        guardrail.screen = AsyncMock(return_value=GuardrailOutcome(text="bad", blocked=True))
        with ExitStack() as stack:
            stack.enter_context(patch(f"{_SERVICE}.bedrock_guardrail", guardrail))
            cfg = stack.enter_context(patch(f"{_SERVICE}.settings"))
            cfg.bedrock_guardrail_screen_output = True
            screened = await screen_generated_question(question)
        assert screened is not None
        assert screened.text == ""

    async def test_no_question_is_left_alone(self):
        assert await screen_generated_question(None) is None


class TestQuestionTitlesFor:
    def test_humanises_a_missing_title(self):
        assert question_titles_for([{"key": "property_type", "title": None}]) == {
            "property_type": "Property Type"
        }

    def test_prefers_the_configured_title(self):
        assert question_titles_for([{"key": "location", "title": "Location"}]) == {
            "location": "Location"
        }

    def test_ignores_rows_without_a_string_key(self):
        assert question_titles_for([{"key": None, "title": "x"}, {"title": "y"}]) == {}


class TestRunLlmIntakeTurn:
    async def test_returns_the_turn_result(self):
        with ExitStack() as stack:
            _enter(stack)
            response = await run_llm_intake_turn(
                MagicMock(), session_id=_SESSION_ID, user_input="warehouse in Austin"
            )
        assert response.extracted == {"location": "Austin"}
        assert response.missing_fields == ["property_type"]
        assert response.total_questions == 2
        assert response.is_complete is False

    async def test_question_titles_reach_the_client(self):
        """The side panel labels missing fields with these; undeclared, they vanished."""
        with ExitStack() as stack:
            _enter(stack)
            response = await run_llm_intake_turn(
                MagicMock(), session_id=_SESSION_ID, user_input="warehouse"
            )
        assert response.question_titles == {
            "location": "Location",
            "property_type": "Property Type",
        }
        assert response.skipped_fields == ["budget"]

    async def test_skipped_fields_bookkeeping_stays_out_of_the_criteria(self):
        """It is persisted so the model stops asking, not because the user chose it."""
        with ExitStack() as stack:
            parse, save = _enter(stack)
            response = await run_llm_intake_turn(
                MagicMock(), session_id=_SESSION_ID, user_input="skip the budget"
            )
        assert "_skipped_fields" not in response.criteria
        # ...but it is still written to the session.
        assert "_skipped_fields" in save.await_args.args[2]

    async def test_prior_criteria_are_passed_to_the_model(self):
        """Each turn merges into what came before; dropping this loses the conversation."""
        with ExitStack() as stack:
            parse, _ = _enter(stack, session_row={"criteria": {"location": "Dallas"}})
            await run_llm_intake_turn(
                MagicMock(), session_id=_SESSION_ID, user_input="make it Austin"
            )
        assert parse.await_args.kwargs["current_criteria"] == {"location": "Dallas"}

    async def test_a_non_dict_criteria_column_does_not_break_the_turn(self):
        with ExitStack() as stack:
            parse, _ = _enter(stack, session_row={"criteria": None})
            await run_llm_intake_turn(
                MagicMock(), session_id=_SESSION_ID, user_input="warehouse"
            )
        assert parse.await_args.kwargs["current_criteria"] == {}

    async def test_the_merged_criteria_are_persisted(self):
        with ExitStack() as stack:
            _, save = _enter(stack)
            await run_llm_intake_turn(
                MagicMock(), session_id=_SESSION_ID, user_input="warehouse in Austin"
            )
        assert save.await_count == 1
        assert save.await_args.args[1] == _SESSION_ID

    async def test_provider_failure_propagates_for_the_caller_to_classify(self):
        """The worker reads the status code to decide retryable vs terminal (§14.1)."""
        failing = AsyncMock(side_effect=HTTPException(status_code=503, detail="busy"))
        with ExitStack() as stack:
            _enter(stack, parse=failing)
            with pytest.raises(HTTPException) as info:
                await run_llm_intake_turn(
                    MagicMock(), session_id=_SESSION_ID, user_input="warehouse"
                )
        assert info.value.status_code == 503

    async def test_nothing_is_persisted_when_the_model_fails(self):
        """A failed turn must not half-write the session it was merging into."""
        failing = AsyncMock(side_effect=HTTPException(status_code=502, detail="bad reply"))
        with ExitStack() as stack:
            _, save = _enter(stack, parse=failing)
            with pytest.raises(HTTPException):
                await run_llm_intake_turn(
                    MagicMock(), session_id=_SESSION_ID, user_input="warehouse"
                )
        save.assert_not_awaited()
