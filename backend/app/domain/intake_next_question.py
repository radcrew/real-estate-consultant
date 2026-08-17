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


def pending_question_key(
    questions: list[QuestionRow],
    *,
    answered: dict[str, Any],
    required_fields: list[str],
    skipped: list[str],
) -> str | None:
    """The question the user is answering this turn, or None when none is outstanding.

    The same rule ``resolve_next_intake_question`` uses to choose what to ask: the first
    required field, in questionnaire order, that is neither answered nor skipped. Derived
    rather than passed in, so it cannot disagree with what was actually asked.

    This reaches the model. Without it a reply of "10" to "What size are you looking for
    (in square feet)?" is unattributable -- nothing in the turn payload says which
    question was put -- and the model guessed ``price``, then echoed the stored budget
    back on every following turn.
    """
    outstanding = [
        key for key in required_fields if key not in answered and key not in skipped
    ]
    row = first_question_row_in_missing(questions, outstanding)
    key = row.get("key") if row else None
    return key if isinstance(key, str) else None
