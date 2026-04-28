"""Build JSON Schema text for LLM intake parsing from ``public.questions`` rows."""

from __future__ import annotations

import json
from typing import Any

from pydantic import TypeAdapter

from app.repositories.questions import sorted_intake_questions
from app.schemas.llm_intake_parse import LlmParseNextQuestion


def question_criteria_keys(questions: list[dict]) -> list[str]:
    keys: list[str] = []
    for row in sorted_intake_questions(questions):
        k = row.get("key")
        if isinstance(k, str) and k.strip():
            keys.append(k.strip())
    return keys


def required_criteria_keys_for_llm(questions: list[dict]) -> list[str]:
    """Keys the model should treat as required until filled.

    Uses each row's ``required`` flag. If no row is marked required, every question
    key is treated as required so the LLM funnel matches the configured questionnaire.
    """
    ordered = sorted_intake_questions(questions)
    flagged: list[str] = []
    for row in ordered:
        k = row.get("key")
        if not isinstance(k, str) or not k.strip():
            continue
        if bool(row.get("required")):
            flagged.append(k.strip())
    if flagged:
        return flagged
    return question_criteria_keys(questions)


def _json_type_for_question_row(row: dict) -> dict[str, Any]:
    """Map a question ``type`` (and optional ``options``) to a JSON Schema fragment."""
    raw_type = row.get("type")
    qtype = raw_type.strip().lower() if isinstance(raw_type, str) else "text"
    options = row.get("options")
    opt_list: list[str] = []
    if isinstance(options, list):
        opt_list = [str(x) for x in options if isinstance(x, (str, int, float))]

    if qtype in ("location", "geo", "address"):
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

    if qtype in ("range", "numeric_range", "sqft_range", "rent_range", "size_range"):
        return {
            "type": "object",
            "description": "Numeric bounds; omit keys or use null when unknown.",
            "properties": {
                "min": {"type": "number"},
                "max": {"type": "number"},
            },
        }

    if qtype in ("multiselect", "multi_select", "tags", "checkboxes", "building_types"):
        frag: dict[str, Any] = {
            "type": "array",
            "items": {"type": "string"},
        }
        if opt_list:
            frag["description"] = f"Prefer one or more of: {', '.join(opt_list)}"
        return frag

    if qtype in ("number", "integer", "float"):
        return {"type": "number"}

    if qtype in ("boolean", "bool"):
        return {"type": "boolean"}

    if qtype in ("select", "single_choice", "radio") and opt_list:
        return {"type": "string", "enum": opt_list}

    return {"type": "string"}


def build_intake_parse_json_schema(*, questions: list[dict]) -> dict[str, Any]:
    """Full JSON Schema for the model response (``extracted`` keys follow Supabase rows)."""
    ordered = sorted_intake_questions(questions)
    extracted_properties: dict[str, Any] = {}
    for row in ordered:
        k = row.get("key")
        if not isinstance(k, str) or not k.strip():
            continue
        key = k.strip()
        frag = _json_type_for_question_row(row)
        qtext = row.get("text")
        if isinstance(qtext, str) and qtext.strip():
            desc = frag.get("description")
            hint = f"Question: {qtext.strip()}"
            frag["description"] = f"{hint}. {desc}" if desc else hint
        extracted_properties[key] = frag

    next_q_schema = TypeAdapter(LlmParseNextQuestion).json_schema()

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "extracted": {
                "type": "object",
                "additionalProperties": False,
                "description": (
                    "Sparse answers keyed by criteria field name (see questionnaire). "
                    "Omit a property entirely when unknown."
                ),
                "properties": extracted_properties,
            },
            "missing_fields": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Subset of required criteria keys that are still unknown.",
            },
            "next_question": next_q_schema,
            "is_complete": {"type": "boolean"},
        },
        "required": ["extracted", "missing_fields", "next_question", "is_complete"],
    }


def format_intake_parse_schema_for_prompt(*, questions: list[dict]) -> str:
    """Indented JSON Schema string embedded in the system prompt."""
    schema = build_intake_parse_json_schema(questions=questions)
    return json.dumps(schema, indent=2, ensure_ascii=True)
