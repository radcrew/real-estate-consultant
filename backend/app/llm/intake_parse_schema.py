"""Build JSON Schema text for LLM intake parsing from `public.questions` rows."""

from __future__ import annotations

import json
from typing import Any, Iterable

from pydantic import TypeAdapter

from app.repositories.questions import sorted_intake_questions
from app.schemas.llm_intake_parse import LlmParseNextQuestion


def _valid_key(row: dict) -> str | None:
    key = row.get("key")
    return key.strip() if isinstance(key, str) and key.strip() else None


def _string_options(options: Any) -> list[str]:
    if isinstance(options, list):
        return [str(x) for x in options if isinstance(x, (str, int, float))]
    return []


def question_criteria_keys(questions: list[dict]) -> list[str]:
    return [
        key
        for row in sorted_intake_questions(questions)


def required_criteria_keys_for_llm(questions: list[dict]) -> list[str]:
    """Keys the model should treat as required until filled."""
    ordered = sorted_intake_questions(questions)

    required_keys = [
        key
        for row in ordered
        if (key := _valid_key(row)) and row.get("required")
    ]

    return required_keys or question_criteria_keys(questions)


# -----------------------------
# Schema builders
# -----------------------------
def _json_type_for_question_row(row: dict) -> dict[str, Any]:
    raw_type = row.get("type")
    qtype = raw_type.strip().lower() if isinstance(raw_type, str) else "text"
    options = _string_options(row.get("options"))

    if qtype in {"location", "geo", "address"}:
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

    if qtype in {"range", "numeric_range", "sqft_range", "rent_range", "size_range"}:
        return {
            "type": "object",
            "description": "Numeric bounds; omit keys or use null when unknown.",
            "properties": {
                "min": {"type": "number"},
                "max": {"type": "number"},
            },
        }

    if qtype in {"multiselect", "multi_select", "tags", "checkboxes", "building_types"}:
        schema: dict[str, Any] = {
            "type": "array",
            "items": {"type": "string"},
        }
        if options:
            schema["description"] = f"Prefer one or more of: {', '.join(options)}"
        return schema

    if qtype in {"number", "integer", "float"}:
        return {"type": "number"}

    if qtype in {"boolean", "bool"}:
        return {"type": "boolean"}

    if qtype in {"select", "single_choice", "radio"} and options:
        return {"type": "string", "enum": options}

    return {"type": "string"}


def build_intake_parse_json_schema(*, questions: list[dict]) -> dict[str, Any]:
    ordered = sorted_intake_questions(questions)

    extracted_properties = {
        key: _with_question_description(_json_type_for_question_row(row), row)
        for row in ordered
        if (key := _valid_key(row))
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


def _with_question_description(schema: dict[str, Any], row: dict) -> dict[str, Any]:
    text = row.get("text")
    if isinstance(text, str) and text.strip():
        hint = f"Question: {text.strip()}"
        desc = schema.get("description")
        schema["description"] = f"{hint}. {desc}" if desc else hint
    return schema


def format_intake_parse_schema_for_prompt(*, questions: list[dict]) -> str:
    return json.dumps(
        build_intake_parse_json_schema(questions=questions),
        indent=2,
        ensure_ascii=True,
    )