"""Match questionnaire rows to LLM ``next_question`` hints (keys / text)."""

from __future__ import annotations

from typing import Any

QuestionRow = dict[str, Any]


def suggested_question_as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def find_question_row_by_key(
    questions: list[QuestionRow],
    question_key: str,
) -> QuestionRow | None:
    for row in questions:
        if row.get("key") == question_key:
            return row
    return None


def match_row_for_text_suggestion(
    questions: list[QuestionRow],
    *,
    suggested_key: object,
    missing_fields: list[str],
) -> QuestionRow | None:
    """Pick a row for LLM question text: try ``suggested_key``, else first missing field key."""
    matched = (
        find_question_row_by_key(questions, suggested_key)
        if isinstance(suggested_key, str)
        else None
    )
    if matched is None and missing_fields:
        matched = find_question_row_by_key(questions, missing_fields[0])
    return matched


def first_question_row_in_missing(
    questions: list[QuestionRow],
    missing_fields: list[str],
) -> QuestionRow | None:
    """First configured question whose key appears in ``missing_fields``."""
    missing = set(missing_fields)
    for row in questions:
        row_key = row.get("key")
        if isinstance(row_key, str) and row_key in missing:
            return row
    return None
