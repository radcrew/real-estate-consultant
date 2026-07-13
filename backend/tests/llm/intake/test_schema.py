"""Tests for app.llm.intake.schema — JSON schema builders for intake prompts."""
from __future__ import annotations

import json

import pytest

from app.llm.intake.schema import (
    build_intake_response_schema,
    extract_question_keys,
    render_intake_response_schema,
)


def _q(key: str, type: str = "text", order: int = 0, required: bool = False, **kwargs) -> dict:
    return {"key": key, "type": type, "order_index": order, "required": required, **kwargs}


# ---------------------------------------------------------------------------
# extract_question_keys
# ---------------------------------------------------------------------------

class TestExtractQuestionKeys:
    def test_returns_all_keys_in_order(self):
        questions = [_q("budget", order=2), _q("location", order=1)]
        keys, required = extract_question_keys(questions)
        assert keys == ["location", "budget"]

    def test_required_subset_when_marked(self):
        questions = [
            _q("location", order=1, required=True),
            _q("budget", order=2, required=False),
        ]
        keys, required = extract_question_keys(questions)
        assert required == ["location"]
        assert "budget" in keys

    def test_required_fallback_to_all_when_none_marked(self):
        questions = [_q("a", order=1), _q("b", order=2)]
        keys, required = extract_question_keys(questions)
        assert required == keys

    def test_blank_key_is_skipped(self):
        questions = [{"key": "  ", "type": "text", "order_index": 1}]
        keys, _ = extract_question_keys(questions)
        assert keys == []

    def test_missing_key_field_is_skipped(self):
        questions = [{"type": "text", "order_index": 0}]
        keys, _ = extract_question_keys(questions)
        assert keys == []

    def test_empty_list_returns_empty(self):
        keys, required = extract_question_keys([])
        assert keys == [] and required == []


# ---------------------------------------------------------------------------
# build_intake_response_schema — property schemas per question type
# ---------------------------------------------------------------------------

class TestBuildIntakeResponseSchema:
    def _props(self, questions):
        schema = build_intake_response_schema(questions=questions)
        return schema["properties"]["extracted"]["properties"]

    def test_top_level_required_keys_present(self):
        schema = build_intake_response_schema(questions=[_q("loc", "location", 1)])
        assert set(schema["required"]) == {
            "extracted", "missing_fields", "skipped_fields", "next_question", "is_complete"
        }

    def test_location_type_produces_string_schema(self):
        props = self._props([_q("loc", "location", 1)])
        assert props["loc"]["type"] == "string"

    def test_geo_type_produces_string_schema(self):
        props = self._props([_q("area", "geo", 1)])
        assert props["area"]["type"] == "string"

    def test_range_type_produces_object_schema(self):
        props = self._props([_q("price", "range", 1)])
        assert props["price"]["type"] == "object"
        assert "min" in props["price"]["properties"]
        assert "max" in props["price"]["properties"]

    def test_sqft_range_type_produces_object_schema(self):
        props = self._props([_q("sqft", "sqft_range", 1)])
        assert props["sqft"]["type"] == "object"

    def test_multiselect_type_produces_array_schema(self):
        props = self._props([_q("amenities", "multiselect", 1)])
        assert props["amenities"]["type"] == "array"
        assert props["amenities"]["items"] == {"type": "string"}

    def test_multiselect_with_options_includes_description(self):
        props = self._props([_q("amenities", "multiselect", 1, options=["pool", "gym"])])
        assert "pool" in props["amenities"].get("description", "")

    def test_number_type_produces_number_schema(self):
        props = self._props([_q("beds", "number", 1)])
        assert props["beds"]["type"] == "number"

    def test_boolean_type_produces_boolean_schema(self):
        props = self._props([_q("furnished", "boolean", 1)])
        assert props["furnished"]["type"] == "boolean"

    def test_select_with_options_produces_enum(self):
        props = self._props([_q("style", "select", 1, options=["modern", "traditional"])])
        assert props["style"].get("enum") == ["modern", "traditional"]

    def test_select_without_options_produces_plain_string(self):
        props = self._props([_q("style", "select", 1)])
        assert props["style"]["type"] == "string"
        assert "enum" not in props["style"]

    def test_unknown_type_falls_back_to_string(self):
        props = self._props([_q("misc", "custom_weird_type", 1)])
        assert props["misc"]["type"] == "string"

    def test_question_text_added_to_description(self):
        q = _q("loc", "text", 1, text="Where do you want to live?")
        props = self._props([q])
        assert "Where do you want to live?" in props["loc"].get("description", "")

    def test_multiple_questions_all_appear(self):
        props = self._props([_q("a", order=1), _q("b", order=2)])
        assert "a" in props and "b" in props

    def test_questions_ordered_by_order_index(self):
        props = self._props([_q("second", order=2), _q("first", order=1)])
        assert list(props.keys()) == ["first", "second"]


# ---------------------------------------------------------------------------
# render_intake_response_schema
# ---------------------------------------------------------------------------

class TestRenderIntakeResponseSchema:
    def test_returns_valid_json_string(self):
        output = render_intake_response_schema(questions=[_q("loc", "location", 1)])
        parsed = json.loads(output)
        assert parsed["type"] == "object"

    def test_ensure_ascii_encoding(self):
        q = _q("loc", "text", 1, text="Où voulez-vous vivre?")
        output = render_intake_response_schema(questions=[q])
        assert all(ord(c) < 128 for c in output)
