"""JSON Schema builders for intake extraction prompts."""

from __future__ import annotations

import json
from typing import Any

from pydantic import TypeAdapter

from app.repositories.questions import sorted_intake_questions
from app.schemas.llm_intake_parse import LlmParseNextQuestion

QuestionRow = dict[str, Any]


def _question_key(row: QuestionRow) -> str | None:
    key = row.get("key")
    return key.strip() if isinstance(key, str) and key.strip() else None


def _string_options(options: Any) -> list[str]:
    if isinstance(options, list):
        return [str(value) for value in options if isinstance(value, (str, int, float))]
    return []


def list_available_question_keys(questions: list[QuestionRow]) -> list[str]:
    return [
        key
        for row in sorted_intake_questions(questions)
        if (key := _question_key(row))
    ]


def list_required_question_keys(questions: list[QuestionRow]) -> list[str]:
    """Keys the model should continue treating as required until they are filled."""
    ordered_questions = sorted_intake_questions(questions)
    required_keys = [
        key
        for row in ordered_questions
        if (key := _question_key(row)) and row.get("required")
    ]
    return required_keys or list_available_question_keys(questions)


def _build_question_value_schema(row: QuestionRow) -> dict[str, Any]:
    raw_type = row.get("type")
    question_type = raw_type.strip().lower() if isinstance(raw_type, str) else "text"
    options = _string_options(row.get("options"))

    if question_type in {"location", "geo", "address"}:
        return {
            "type": "object",
            "description": (
                "Geographic intent; use null for unknown lat/lng. "
                "label should name the city, region, or address phrase."
            ),
            "properties": {
                "label": {"type": "string"},
                "lat": {"type": "number"},
                "lng": {"type": "number"},
            },
        }

    if question_type in {"range", "numeric_range", "sqft_range", "rent_range", "size_range"}:
        return {
            "type": "object",
            "description": "Numeric bounds; omit keys or use null when unknown.",
            "properties": {
                "min": {"type": "number"},
                "max": {"type": "number"},
            },
        }

    if question_type in {"multiselect", "multi_select", "tags", "checkboxes", "building_types"}:
        schema: dict[str, Any] = {
            "type": "array",
            "items": {"type": "string"},
        }
        if options:
            schema["description"] = f"Prefer one or more of: {', '.join(options)}"
        return schema

    if question_type in {"number", "integer", "float"}:
        return {"type": "number"}

    if question_type in {"boolean", "bool"}:
        return {"type": "boolean"}

    if question_type in {"select", "single_choice", "radio"} and options:
        return {"type": "string", "enum": options}

    return {"type": "string"}


def _add_question_description(schema: dict[str, Any], row: QuestionRow) -> dict[str, Any]:
    text = row.get("text")
    if isinstance(text, str) and text.strip():
        description = f"Question: {text.strip()}"
        existing = schema.get("description")
        schema["description"] = f"{description}. {existing}" if existing else description
    return schema


def build_intake_response_schema(*, questions: list[QuestionRow]) -> dict[str, Any]:
    ordered_questions = sorted_intake_questions(questions)
    extracted_properties = {
        key: _add_question_description(_build_question_value_schema(row), row)
        for row in ordered_questions
        if (key := _question_key(row))
    }

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "extracted": {
                "type": "object",
                "additionalProperties": False,
                "description": (
                    "Sparse answers keyed by criteria field name. "
                    "Omit properties when unknown."
                ),
                "properties": extracted_properties,
            },
            "missing_fields": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Required criteria keys still missing.",
            },
            "next_question": TypeAdapter(LlmParseNextQuestion).json_schema(),
            "is_complete": {"type": "boolean"},
        },
        "required": ["extracted", "missing_fields", "next_question", "is_complete"],
    }


def render_intake_response_schema(*, questions: list[QuestionRow]) -> str:
    return json.dumps(
        build_intake_response_schema(questions=questions),
        indent=2,
        ensure_ascii=True,
    )
