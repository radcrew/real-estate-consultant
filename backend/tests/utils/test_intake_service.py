"""Tests for app.llm.intake.service — intake orchestration."""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.llm.intake.service import (
    SKIPPED_FIELDS_KEY,
    _build_intake_parse_result,
    generate_opening_question,
    parse_user_input,
    resolve_next_intake_question,
)
from app.schemas.intake_sessions import IntakeSessionFirstQuestion
from app.schemas.llm_intake_parse import LlmOpeningQuestionOutput, LlmParseModelOutput


def _q(key: str, type: str = "text", order: int = 0, required: bool = False, **kw) -> dict:
    return {"key": key, "type": type, "order_index": order, "required": required, **kw}


def _parsed_output(
    extracted: dict | None = None,
    missing: list | None = None,
    skipped: list | None = None,
    next_key: str | None = None,
    next_text: str | None = None,
    is_complete: bool = False,
) -> LlmParseModelOutput:
    return LlmParseModelOutput(
        extracted=extracted or {},
        missing_fields=missing or [],
        skipped_fields=skipped or [],
        next_question={"key": next_key, "text": next_text},
        is_complete=is_complete,
    )


# ---------------------------------------------------------------------------
# _build_intake_parse_result
# ---------------------------------------------------------------------------

class TestBuildIntakeParseResult:
    def _call(self, parsed, question_keys, current_criteria=None, required_fields=None, previously_skipped=None):
        return _build_intake_parse_result(
            parsed_output=parsed,
            question_keys=question_keys or [],
            current_criteria=current_criteria or {},
            required_fields=required_fields or [],
            previously_skipped=previously_skipped or [],
        )

    def test_basic_extraction_merges_into_criteria(self):
        parsed = _parsed_output(extracted={"location": "Austin"})
        result = self._call(parsed, ["location"], required_fields=["location"])
        assert result["merged_criteria"]["location"] == "Austin"

    def test_extracted_keys_filtered_to_allowed(self):
        parsed = _parsed_output(extracted={"location": "Austin", "unknown_key": "xyz"})
        result = self._call(parsed, ["location"])
        assert "unknown_key" not in result["extracted"]
        assert result["extracted"]["location"] == "Austin"

    def test_merged_criteria_preserves_existing(self):
        parsed = _parsed_output(extracted={"beds": 2})
        result = self._call(parsed, ["beds", "location"], current_criteria={"location": "LA"}, required_fields=["beds", "location"])
        assert result["merged_criteria"]["location"] == "LA"
        assert result["merged_criteria"]["beds"] == 2

    def test_is_complete_true_when_no_missing(self):
        parsed = _parsed_output(extracted={"location": "NYC"})
        result = self._call(parsed, ["location"], current_criteria={"location": "NYC"}, required_fields=["location"])
        assert result["is_complete"] is True

    def test_is_complete_false_when_missing_fields(self):
        parsed = _parsed_output()
        result = self._call(parsed, ["location"], required_fields=["location"])
        assert result["is_complete"] is False

    def test_skipped_fields_added_to_merged_criteria(self):
        parsed = _parsed_output(skipped=["budget"])
        result = self._call(parsed, ["budget"], required_fields=["budget"])
        assert SKIPPED_FIELDS_KEY in result["merged_criteria"]
        assert "budget" in result["merged_criteria"][SKIPPED_FIELDS_KEY]

    def test_previously_skipped_preserved(self):
        parsed = _parsed_output(skipped=[])
        result = self._call(
            parsed, ["location", "budget"],
            required_fields=["location", "budget"],
            previously_skipped=["location"],
        )
        assert "location" in result["skipped_fields"]

    def test_next_question_in_result(self):
        parsed = _parsed_output(next_key="budget", next_text="What is your budget?")
        result = self._call(parsed, ["budget"])
        assert result["next_question"]["key"] == "budget"


# ---------------------------------------------------------------------------
# resolve_next_intake_question
# ---------------------------------------------------------------------------

class TestResolveNextIntakeQuestion:
    _QUESTIONS = [
        _q("location", "text", order=1, text="Where?", title="Location"),
        _q("budget", "range", order=2, text="Budget?", title="Budget"),
    ]

    def test_text_suggestion_returns_first_question(self):
        result = resolve_next_intake_question(
            questions=self._QUESTIONS,
            suggested_question={"key": "location", "text": "Where would you like to live?"},
            missing_fields=["location"],
        )
        assert isinstance(result, IntakeSessionFirstQuestion)
        assert result.text == "Where would you like to live?"
        assert result.key == "location"

    def test_text_suggestion_without_matching_key_uses_missing_field(self):
        result = resolve_next_intake_question(
            questions=self._QUESTIONS,
            suggested_question={"key": None, "text": "Tell me about your preferences."},
            missing_fields=["budget"],
        )
        assert isinstance(result, IntakeSessionFirstQuestion)
        assert result.key == "budget"

    def test_key_suggestion_returns_mapped_row(self):
        result = resolve_next_intake_question(
            questions=self._QUESTIONS,
            suggested_question={"key": "budget", "text": None},
            missing_fields=["budget"],
        )
        assert isinstance(result, IntakeSessionFirstQuestion)
        assert result.key == "budget"

    def test_unknown_key_suggestion_falls_back_to_missing(self):
        result = resolve_next_intake_question(
            questions=self._QUESTIONS,
            suggested_question={"key": "nonexistent", "text": None},
            missing_fields=["location"],
        )
        assert result is not None
        assert result.key == "location"

    def test_returns_none_when_nothing_matches(self):
        result = resolve_next_intake_question(
            questions=[],
            suggested_question={"key": None, "text": None},
            missing_fields=[],
        )
        assert result is None

    def test_empty_text_suggestion_falls_through_to_key(self):
        result = resolve_next_intake_question(
            questions=self._QUESTIONS,
            suggested_question={"key": "location", "text": "   "},
            missing_fields=["location"],
        )
        # "   ".strip() is "" → falsy → falls to key branch
        assert result is not None
        assert result.key == "location"


# ---------------------------------------------------------------------------
# generate_opening_question
# ---------------------------------------------------------------------------

class TestGenerateOpeningQuestion:
    async def test_returns_stripped_text(self):
        mock_output = LlmOpeningQuestionOutput(text="  Hello! What city?  ")
        with patch(
            "app.llm.intake.service.huggingface_provider.generate_structured_output",
            new_callable=AsyncMock,
            return_value=mock_output,
        ):
            result = await generate_opening_question(
                welcome_message="Welcome",
                key="location",
                type="location",
            )
        assert result == "Hello! What city?"

    async def test_empty_text_raises_502(self):
        mock_output = LlmOpeningQuestionOutput(text="")
        with patch(
            "app.llm.intake.service.huggingface_provider.generate_structured_output",
            new_callable=AsyncMock,
            return_value=mock_output,
        ):
            with pytest.raises(HTTPException) as info:
                await generate_opening_question(
                    welcome_message="Welcome",
                    key="location",
                    type="location",
                )
        assert info.value.status_code == 502

    async def test_options_appends_hint_to_system_prompt(self):
        mock_output = LlmOpeningQuestionOutput(text="Choose one:")
        with patch(
            "app.llm.intake.service.huggingface_provider.generate_structured_output",
            new_callable=AsyncMock,
            return_value=mock_output,
        ) as mock_gen:
            await generate_opening_question(
                welcome_message="Hi",
                key="style",
                type="select",
                options=["modern", "classic"],
            )
        call_kwargs = mock_gen.call_args.kwargs
        messages = call_kwargs["messages"]
        system_content = messages[0]["content"]
        user_content = messages[1]["content"]
        assert "modern" in user_content or "classic" in user_content

    async def test_no_options_user_payload_excludes_options_field(self):
        mock_output = LlmOpeningQuestionOutput(text="Where?")
        with patch(
            "app.llm.intake.service.huggingface_provider.generate_structured_output",
            new_callable=AsyncMock,
            return_value=mock_output,
        ) as mock_gen:
            await generate_opening_question(
                welcome_message="Hi",
                key="location",
                type="location",
            )
        call_kwargs = mock_gen.call_args.kwargs
        user_content = call_kwargs["messages"][1]["content"]
        import json
        payload = json.loads(user_content)
        assert "question_options" not in payload


# ---------------------------------------------------------------------------
# parse_user_input
# ---------------------------------------------------------------------------

class TestParseUserInput:
    _QUESTIONS = [
        _q("location", "location", order=1, required=True),
        _q("budget", "range", order=2, required=True),
    ]

    async def test_returns_structured_result(self):
        mock_output = _parsed_output(
            extracted={"location": "Austin"},
            missing=["budget"],
        )
        with patch(
            "app.llm.intake.service.huggingface_provider.generate_structured_output",
            new_callable=AsyncMock,
            return_value=mock_output,
        ):
            result = await parse_user_input(
                user_input="I want to live in Austin",
                current_criteria={},
                questions=self._QUESTIONS,
            )
        assert result["extracted"]["location"] == "Austin"
        assert "budget" in result["missing_fields"]
        assert result["is_complete"] is False

    async def test_previously_skipped_excluded_from_criteria_for_prompt(self):
        mock_output = _parsed_output()
        with patch(
            "app.llm.intake.service.huggingface_provider.generate_structured_output",
            new_callable=AsyncMock,
            return_value=mock_output,
        ) as mock_gen:
            await parse_user_input(
                user_input="skip budget",
                current_criteria={SKIPPED_FIELDS_KEY: ["budget"], "location": "NYC"},
                questions=self._QUESTIONS,
            )
        call_kwargs = mock_gen.call_args.kwargs
        import json
        payload = json.loads(call_kwargs["messages"][1]["content"])
        # SKIPPED_FIELDS_KEY should be excluded from current_criteria in prompt
        assert SKIPPED_FIELDS_KEY not in payload["current_criteria"]
        assert payload["previously_skipped_fields"] == ["budget"]

    async def test_complete_criteria_returns_is_complete_true(self):
        mock_output = _parsed_output(
            extracted={"budget": {"min": 100000}},
            is_complete=True,
        )
        with patch(
            "app.llm.intake.service.huggingface_provider.generate_structured_output",
            new_callable=AsyncMock,
            return_value=mock_output,
        ):
            result = await parse_user_input(
                user_input="My budget is 100k to 200k",
                current_criteria={"location": "Austin"},
                questions=self._QUESTIONS,
            )
        # both required fields now filled
        assert result["is_complete"] is True
