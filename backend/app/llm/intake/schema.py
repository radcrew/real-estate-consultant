"""JSON Schema builders for intake extraction prompts."""

from __future__ import annotations

import json
from typing import Any

from app.repositories.questions import sorted_intake_questions

QuestionRow = dict[str, Any]


def _question_key(row: QuestionRow) -> str | None:
    key = row.get("key")
    return key.strip() if isinstance(key, str) and key.strip() else None


def _string_options(options: Any) -> list[str]:
    """Selectable choices for a question, as the values the backend stores.

    Rows come in two shapes: ``ml/eval/questions.json`` used plain strings, the database
    uses ``{"label": "Industrial", "value": "industrial"}``. Reading only the string form
    made this return ``[]`` for every real question, so the prompt listed no options and
    the model had to guess the vocabulary — it answered "warehouse" for a questionnaire
    that only offers "industrial", and the answer was then dropped as unconfigured.
    """
    if not isinstance(options, list):
        return []
    chosen: list[str] = []
    for option in options:
        if isinstance(option, dict):
            option = next(
                (text for key in ("value", "label")
                 if isinstance(text := option.get(key), str) and text.strip()),
                None,
            )
        if isinstance(option, (str, int, float)) and str(option).strip():
            chosen.append(str(option).strip())
    return chosen


def extract_question_keys(
    questions: list[QuestionRow],
) -> tuple[list[str], list[str]]:
    """Return (all question keys in order, keys treated as required until filled).

    If no rows are marked required, required_fields matches the full key list.
    """
    ordered_questions = sorted_intake_questions(questions)
    available = [
        key
        for row in ordered_questions
        if (key := _question_key(row))
    ]
    required = [
        key
        for row in ordered_questions
        if (key := _question_key(row)) and row.get("required")
    ]
    required_fields = required or available
    return available, required_fields


def _build_question_value_schema(row: QuestionRow) -> dict[str, Any]:
    raw_type = row.get("type")
    question_type = raw_type.strip().lower() if isinstance(raw_type, str) else "text"
    options = _string_options(row.get("options"))

    if question_type in {"location", "geo", "address"}:
        return {
            "type": "string",
            "description": (
                "Copy only the place the message states; never add a region it omits."
            ),
        }

    if question_type in {"range", "numeric_range", "sqft_range", "rent_range", "size_range"}:
        # No description on purpose. "Numeric bounds" restates the type, and the clause
        # that used to follow it -- "omit keys or use null when unknown" -- contradicted
        # both `min`/`max` being typed `number` (null is not a number) and the training
        # set, where 0 of 2160 targets carry a null bound. Models took the invitation and
        # emitted {"min": null, "max": null} for fields the message never mentioned.
        return {
            "type": "object",
            "properties": {
                "min": {"type": "number"},
                "max": {"type": "number"},
            },
        }

    if question_type in {
        "multiselect",
        "multi_select",
        "multi-select",
        "tags",
        "checkboxes",
        "building_types",
    }:
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
    """Append the question this field answers, **after** any extraction guidance.

    Order matters. The model copies this string into ``next_question.text`` — see the
    stock-model outputs in ``ml/eval/results/0.5b-stock-q4km.json``, where every leaked
    question is the wording followed by the guidance that trailed it. Putting the
    question last means a copied tail is the question itself, not prompt scaffolding.
    """
    text = row.get("text")
    if isinstance(text, str) and text.strip():
        question = f"Answers: {text.strip()}"
        existing = schema.get("description")
        if existing:
            lead = existing if existing.endswith(".") else f"{existing}."
            schema["description"] = f"{lead} {question}"
        else:
            schema["description"] = question
    return schema


def build_intake_response_schema(*, questions: list[QuestionRow]) -> dict[str, Any]:
    ordered_questions = sorted_intake_questions(questions)
    extracted_properties = {
        key: _add_question_description(_build_question_value_schema(row), row)
        for row in ordered_questions
        if (key := _question_key(row))
    }

    # Only ``extracted`` and ``skipped_fields`` are read. ``missing_fields`` is recomputed
    # by ``merge_missing_fields`` and ``is_complete`` is derived from it, so asking the
    # model for either buys prompt tokens and nothing else.
    #
    # ``next_question`` is asked for but never read — see the note on it below.
    return {
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
            "skipped_fields": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Criteria keys the user explicitly declined to answer. "
                    "Never ask about these again."
                ),
            },
            # Compatibility shim, not a request for content. The v2 adapter was tuned
            # against a three-key object; asking for two makes it emit
            # ``"skipped_fields":[}}`` and 21% of turns fail to parse. The field is
            # required so the shape it learned stays valid, carries no description so
            # there is no prose to copy into a reply, and its value is discarded by
            # ``resolve_next_intake_question``.
            #
            # Delete this once a model trained on the two-key schema is serving.
            "next_question": {
                "type": "object",
                "additionalProperties": False,
                "properties": {"text": {"type": ["string", "null"]}},
            },
        },
        "required": ["extracted", "skipped_fields", "next_question"],
    }


def render_intake_response_schema(*, questions: list[QuestionRow]) -> str:
    return json.dumps(
        build_intake_response_schema(questions=questions),
        indent=2,
        ensure_ascii=True,
    )
