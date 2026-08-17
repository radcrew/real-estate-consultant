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
    pending_question_for,
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
    def _call(self, parsed, question_keys, current_criteria=None, required_fields=None,
              previously_skipped=None, user_input="", questions=None):
        # Both post-filters default to no-ops so unrelated cases stay focused:
        # user_input "" states no bound direction, and questions [] gives the choice
        # filter no configured options to check against. Tests that want either pass it.
        return _build_intake_parse_result(
            parsed_output=parsed,
            user_input=user_input,
            questions=questions or [],
            question_keys=question_keys or [],
            current_criteria=current_criteria or {},
            required_fields=required_fields or [],
            previously_skipped=previously_skipped or [],
        )

    def test_basic_extraction_merges_into_criteria(self):
        parsed = _parsed_output(extracted={"location": "Austin"})
        result = self._call(parsed, ["location"], required_fields=["location"])
        assert result["merged_criteria"]["location"] == "Austin"

    def test_an_unoffered_choice_leaves_the_field_missing(self):
        """Dropping the value must happen before missing_fields, or the session
        completes on a value the property search cannot use."""
        rows = [_q("property_type", "multiselect", order=1, text="Type?", title="Type",
                   options=["Office", "Warehouse"])]
        parsed = _parsed_output(extracted={"property_type": ["house"]})
        result = self._call(
            parsed, ["property_type"], required_fields=["property_type"], questions=rows,
        )
        assert result["extracted"] == {}
        assert result["missing_fields"] == ["property_type"]
        assert result["is_complete"] is False

    def test_an_inverted_bound_is_corrected_from_the_message(self):
        """The model reads the figure reliably and the comparator unreliably."""
        parsed = _parsed_output(extracted={"price": {"min": 2000000}})
        result = self._call(
            parsed, ["price"], required_fields=["price"],
            user_input="cost should be lower than $2M",
        )
        assert result["extracted"]["price"] == {"max": 2000000}
        assert result["merged_criteria"]["price"] == {"max": 2000000}

    def test_each_figure_is_bound_by_its_own_comparator(self):
        """"$2M" is governed by "lower than" even though the message also states a min."""
        parsed = _parsed_output(extracted={"price": {"min": 2000000}})
        result = self._call(
            parsed, ["price"], required_fields=["price"],
            user_input="lower than $2M but higher than $500K",
        )
        assert result["extracted"]["price"] == {"max": 2000000}

    def test_an_invented_bound_is_dropped(self):
        """"less than $1M" states no minimum, so min: 0 came from nowhere."""
        parsed = _parsed_output(extracted={"price": {"min": 0, "max": 1000000}})
        result = self._call(
            parsed, ["price"], required_fields=["price"],
            user_input="costs less than $1M",
        )
        assert result["extracted"]["price"] == {"max": 1000000}

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

class TestPendingQuestionFor:
    """The turn context the parser needs to read a bare answer like "1000"."""

    _QUESTIONS = [
        _q("location", "text", order=1, text="Where?", title="Location"),
        _q("budget", "range", order=2, text="Budget?", title="Budget"),
    ]

    def test_returns_first_unanswered_required_field(self):
        result = pending_question_for(
            self._QUESTIONS,
            criteria={},
            required_fields=["location", "budget"],
            skipped=[],
        )
        assert result == {"key": "location", "text": "Where?"}

    def test_advances_past_answered_fields(self):
        result = pending_question_for(
            self._QUESTIONS,
            criteria={"location": "Austin"},
            required_fields=["location", "budget"],
            skipped=[],
        )
        assert result is not None
        assert result["key"] == "budget"

    def test_skips_declined_fields(self):
        # A skipped field is not open, so a reply cannot be an answer to it.
        result = pending_question_for(
            self._QUESTIONS,
            criteria={},
            required_fields=["location", "budget"],
            skipped=["location"],
        )
        assert result is not None
        assert result["key"] == "budget"

    def test_none_when_nothing_is_open(self):
        result = pending_question_for(
            self._QUESTIONS,
            criteria={"location": "Austin", "budget": {"min": 1}},
            required_fields=["location", "budget"],
            skipped=[],
        )
        assert result is None

    def test_none_when_the_key_has_no_question_row(self):
        result = pending_question_for(
            self._QUESTIONS,
            criteria={},
            required_fields=["nonexistent"],
            skipped=[],
        )
        assert result is None


class TestResolveNextIntakeQuestion:
    _QUESTIONS = [
        _q("location", "text", order=1, text="Where?", title="Location"),
        _q("budget", "range", order=2, text="Budget?", title="Budget"),
    ]

    def test_model_authored_text_is_ignored(self):
        """The model still emits next_question so its JSON stays well formed, but the
        wording comes from the questionnaire — four defects came from trusting it."""
        result = resolve_next_intake_question(
            questions=self._QUESTIONS,
            suggested_question={"key": "location", "text": "Where would you like to live?"},
            missing_fields=["location"],
        )
        assert isinstance(result, IntakeSessionFirstQuestion)
        assert result.key == "location"
        assert result.text == "Where?"

    def test_nothing_missing_means_no_question(self):
        """A completed session kept asking because the model still wrote question text."""
        result = resolve_next_intake_question(
            questions=self._QUESTIONS,
            suggested_question={"key": None, "text": "What is your budget range?"},
            missing_fields=[],
        )
        assert result is None

    def test_text_about_an_answered_field_falls_back_to_canonical(self):
        """The model may word a pending question, never introduce an answered one."""
        result = resolve_next_intake_question(
            questions=self._QUESTIONS,
            suggested_question={"key": "location", "text": "What is your budget range?"},
            missing_fields=["budget"],
        )
        assert isinstance(result, IntakeSessionFirstQuestion)
        assert result.key == "budget"
        assert result.text == "Budget?"

    def test_key_suggestion_for_an_answered_field_is_ignored(self):
        result = resolve_next_intake_question(
            questions=self._QUESTIONS,
            suggested_question={"key": "location", "text": None},
            missing_fields=["budget"],
        )
        assert isinstance(result, IntakeSessionFirstQuestion)
        assert result.key == "budget"

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

    def test_returns_none_once_nothing_is_missing(self):
        # The model keeps suggesting the field it has just collected. Honouring that asks
        # a completed question again, and the intake never ends.
        result = resolve_next_intake_question(
            questions=self._QUESTIONS,
            suggested_question={"key": "budget", "text": "What is your budget?"},
            missing_fields=[],
        )
        assert result is None

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
            "app.llm.intake.service.generate_structured_output",
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
            "app.llm.intake.service.generate_structured_output",
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
            "app.llm.intake.service.generate_structured_output",
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
            "app.llm.intake.service.generate_structured_output",
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
            "app.llm.intake.service.generate_structured_output",
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

    async def test_does_not_ask_the_provider_for_a_second_schema_copy(self):
        mock_output = _parsed_output()
        with patch(
            "app.llm.intake.service.generate_structured_output",
            new_callable=AsyncMock,
            return_value=mock_output,
        ) as mock_gen:
            await parse_user_input(
                user_input="I want to live in Austin",
                current_criteria={},
                questions=self._QUESTIONS,
            )
        assert mock_gen.call_args.kwargs["include_schema_instruction"] is False

    async def test_constant_content_precedes_the_variable_turn_payload(self):
        # A served prefix cache only hits while the schema and rules stay ahead of the
        # per-turn payload. Reordering these silently costs prompt-processing time.
        mock_output = _parsed_output()
        with patch(
            "app.llm.intake.service.generate_structured_output",
            new_callable=AsyncMock,
            return_value=mock_output,
        ) as mock_gen:
            await parse_user_input(
                user_input="I want to live in Austin",
                current_criteria={},
                questions=self._QUESTIONS,
            )
        messages = mock_gen.call_args.kwargs["messages"]
        assert [m["role"] for m in messages] == ["system", "user"]
        assert "JSON Schema" in messages[0]["content"]
        assert "I want to live in Austin" in messages[1]["content"]

    async def test_previously_skipped_excluded_from_criteria_for_prompt(self):
        mock_output = _parsed_output()
        with patch(
            "app.llm.intake.service.generate_structured_output",
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
            "app.llm.intake.service.generate_structured_output",
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


class TestIntakeOverrideWiring:
    """Only parse_user_input takes the pinned endpoint."""

    _QUESTIONS = [
        _q("location", "location", order=1, required=True),
        _q("budget", "range", order=2, required=True),
    ]

    async def test_parse_passes_the_configured_override(self):
        with patch(
            "app.llm.intake.service.generate_structured_output",
            new_callable=AsyncMock,
            return_value=_parsed_output(),
        ) as mock_gen, patch(
            "app.llm.intake.service.settings"
        ) as mock_settings:
            mock_settings.intake_chat_override = ("qwen-intake", "http://box:8080/v1", "k")
            await parse_user_input(
                user_input="Austin",
                current_criteria={},
                questions=self._QUESTIONS,
            )
        kwargs = mock_gen.call_args.kwargs
        assert kwargs["model"] == "qwen-intake"
        assert kwargs["base_url"] == "http://box:8080/v1"
        assert kwargs["api_key"] == "k"

    async def test_parse_sends_no_override_when_unset(self):
        with patch(
            "app.llm.intake.service.generate_structured_output",
            new_callable=AsyncMock,
            return_value=_parsed_output(),
        ) as mock_gen, patch(
            "app.llm.intake.service.settings"
        ) as mock_settings:
            mock_settings.intake_chat_override = None
            await parse_user_input(
                user_input="Austin",
                current_criteria={},
                questions=self._QUESTIONS,
            )
        kwargs = mock_gen.call_args.kwargs
        assert kwargs["model"] is None
        assert kwargs["base_url"] is None
        assert kwargs["api_key"] is None

    async def test_opening_question_never_takes_the_override(self):
        # A 0.5B pinned for extraction must never be asked to write prose.
        with patch(
            "app.llm.intake.service.generate_structured_output",
            new_callable=AsyncMock,
            return_value=LlmOpeningQuestionOutput(text="What are you looking for?"),
        ) as mock_gen, patch(
            "app.llm.intake.service.settings"
        ) as mock_settings:
            mock_settings.intake_chat_override = ("qwen-intake", "http://box:8080/v1", "k")
            await generate_opening_question(
                welcome_message="Welcome", key="location", type="location"
            )
        assert "base_url" not in mock_gen.call_args.kwargs


class TestSkipClearedWhenAnswered:
    """A required field is answered, skipped, or missing - never two at once."""

    def _call(self, parsed, **kw):
        return _build_intake_parse_result(
            parsed_output=parsed,
            user_input=kw.get("user_input", ""),
            questions=kw.get("questions", []),
            question_keys=kw.get("question_keys", ["location", "budget"]),
            current_criteria=kw.get("current_criteria", {}),
            required_fields=kw.get("required_fields", ["location", "budget"]),
            previously_skipped=kw.get("previously_skipped", []),
        )

    def test_answering_a_skipped_field_clears_the_skip(self):
        # Previously this stayed skipped forever: the union carried it across every
        # later turn, so the answer the user gave was ignored by the progress state.
        parsed = _parsed_output(extracted={"location": "Austin"})
        result = self._call(parsed, previously_skipped=["location"])
        assert result["skipped_fields"] == []
        assert result["merged_criteria"]["location"] == "Austin"
        assert SKIPPED_FIELDS_KEY not in result["merged_criteria"]

    def test_a_field_answered_in_an_earlier_turn_is_not_skipped(self):
        parsed = _parsed_output(skipped=["location"])
        result = self._call(parsed, current_criteria={"location": "Austin"})
        assert "location" not in result["skipped_fields"]

    def test_unanswered_skips_still_carry_forward(self):
        parsed = _parsed_output(extracted={"location": "Austin"})
        result = self._call(parsed, previously_skipped=["location", "budget"])
        assert result["skipped_fields"] == ["budget"]

    def test_a_key_never_appears_in_both_skipped_and_missing(self):
        parsed = _parsed_output(extracted={"location": "Austin"})
        result = self._call(parsed, previously_skipped=["location"])
        assert not set(result["skipped_fields"]) & set(result["missing_fields"])

    def test_answering_a_skipped_field_makes_the_session_completable(self):
        # The message has to state the figure. An answer no message supports is stored
        # but not counted as answered, so the empty ``user_input`` the other cases use
        # would leave the budget unconfirmed and the session open.
        parsed = _parsed_output(extracted={"budget": {"max": 100}})
        result = self._call(
            parsed,
            current_criteria={"location": "Austin"},
            previously_skipped=["budget"],
            user_input="up to 100",
        )
        assert result["skipped_fields"] == []
        assert result["missing_fields"] == []
        assert result["is_complete"] is True


# ---------------------------------------------------------------------------
# The third state: stored, but not an answer
# ---------------------------------------------------------------------------

class TestUnconfirmedValues:
    """Missing, unknown and explicit are three states, and the pipeline had two.

    An answer the message supports is explicit. An answer it contradicts is dropped, and
    the field goes back to missing. In between sits a reading nobody can check: the model
    may well be right -- "a depot for our trucks" really is industrial -- but nothing in
    the message says so. Measured across 21 recorded eval runs, a value in that state is
    correct 23% of the time (property type) or 32% (a range), against 88% and 92% for one
    the message evidences.

    So it is stored, and the question is still asked. The user loses nothing and confirms
    rather than retypes.
    """

    _ROWS = [
        _q("location", "location", order=0, required=True, title="Location"),
        _q("property_type", "multi-select", order=1, required=True, title="Type",
           options=[{"label": "Industrial", "value": "industrial"},
                    {"label": "Retail", "value": "retail"}]),
        _q("price", "range", order=2, required=True, title="Budget"),
    ]
    _KEYS = ["location", "property_type", "price"]
    _REQUIRED = ["location", "property_type", "price"]

    def _call(self, parsed, user_input, current_criteria=None, previously_skipped=None):
        return _build_intake_parse_result(
            parsed_output=parsed,
            user_input=user_input,
            questions=self._ROWS,
            question_keys=self._KEYS,
            current_criteria=current_criteria or {},
            required_fields=self._REQUIRED,
            previously_skipped=previously_skipped or [],
        )

    def test_the_reported_message_asks_rather_than_assumes(self):
        """The bug, end to end. Nothing in the message names a property type."""
        parsed = _parsed_output(
            extracted={"property_type": ["industrial"]},
            missing=["location", "price"],
        )
        result = self._call(parsed, "at least 20 dock doors")
        assert result["unconfirmed_fields"] == ["property_type"]
        assert "property_type" in result["missing_fields"]
        assert result["is_complete"] is False
        # Stored, so the client can offer it back instead of asking from scratch.
        assert result["merged_criteria"]["property_type"] == ["industrial"]

    def test_a_type_the_message_names_is_an_answer(self):
        parsed = _parsed_output(extracted={"property_type": ["industrial"]})
        result = self._call(parsed, "a warehouse with 20 dock doors")
        assert result["unconfirmed_fields"] == []
        assert "property_type" not in result["missing_fields"]

    def test_a_generalisation_is_still_only_a_reading(self):
        """"depot" is industrial and the model is right -- and cannot be checked."""
        parsed = _parsed_output(extracted={"property_type": ["industrial"]})
        result = self._call(parsed, "a depot for our trucks")
        assert result["unconfirmed_fields"] == ["property_type"]
        assert result["merged_criteria"]["property_type"] == ["industrial"]

    def test_a_figure_the_parser_cannot_read_is_stored_and_asked_about(self):
        """The source document's own example of ambiguous: "around a million"."""
        parsed = _parsed_output(extracted={"price": {"max": 1000000}})
        result = self._call(parsed, "something around a million")
        assert result["unconfirmed_fields"] == ["price"]
        assert result["merged_criteria"]["price"] == {"max": 1000000}

    def test_a_figure_the_message_states_is_an_answer(self):
        parsed = _parsed_output(extracted={"price": {"max": 1000000}})
        result = self._call(parsed, "my budget is up to $1M")
        assert result["unconfirmed_fields"] == []

    def test_the_model_cannot_talk_its_way_out_of_being_asked(self):
        """``merge_missing_fields`` narrows to the model's own list when they overlap.

        An unconfirmed field has to survive that narrowing, because the model believing
        it answered the field is the failure being corrected.
        """
        parsed = _parsed_output(
            extracted={"property_type": ["industrial"]},
            missing=["location"],
        )
        result = self._call(parsed, "at least 20 dock doors")
        assert "property_type" in result["missing_fields"]

    def test_a_field_is_only_questioned_once(self):
        """Carried forward means it was asked about when it arrived.

        Without this the same unconfirmable answer is re-questioned every turn, and a
        user who keeps saying "around a million" is never allowed to finish.
        """
        parsed = _parsed_output(extracted={"price": {"max": 1000000}})
        result = self._call(
            parsed, "still around a million", current_criteria={"price": {"max": 1000000}}
        )
        assert result["unconfirmed_fields"] == []

    def test_a_guess_does_not_undo_a_skip(self):
        """The user declined this field. A reading nobody can check is not them
        changing their mind, and clearing the skip would put the question back."""
        parsed = _parsed_output(extracted={"property_type": ["industrial"]})
        result = self._call(
            parsed, "at least 20 dock doors", previously_skipped=["property_type"]
        )
        assert result["skipped_fields"] == ["property_type"]
        assert result["unconfirmed_fields"] == []
        assert "property_type" not in result["missing_fields"]

    def test_a_real_answer_still_undoes_a_skip(self):
        parsed = _parsed_output(extracted={"property_type": ["industrial"]})
        result = self._call(
            parsed, "a warehouse please", previously_skipped=["property_type"]
        )
        assert result["skipped_fields"] == []
        assert "property_type" not in result["missing_fields"]
