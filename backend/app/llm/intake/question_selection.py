"""Question selection helpers for the intake flow."""

from __future__ import annotations

from typing import Any

from app.repositories.questions import map_question_to_model
from app.schemas.intake_sessions import IntakeSessionFirstQuestion

QuestionRow = dict[str, Any]


def find_question_row_by_key(
    questions: list[QuestionRow],
    question_key: str,
) -> QuestionRow | None:
    for row in questions:
        if row.get("key") == question_key:
            return row
    return None


def choose_next_intake_question(
    questions: list[QuestionRow],
    suggested_question: object,
    missing_fields: list[str],
) -> IntakeSessionFirstQuestion | None:
    """Prefer LLM-authored text while anchoring the result to a known question row."""
    if not isinstance(suggested_question, dict):
        suggested_question = {}

    suggested_key = suggested_question.get("key")
    suggested_text = suggested_question.get("text")

    if isinstance(suggested_text, str) and suggested_text.strip():
        question_text = suggested_text.strip()
        matched_row = (
            find_question_row_by_key(questions, suggested_key)
            if isinstance(suggested_key, str)
            else None
        )
        if matched_row is None and missing_fields:
            matched_row = find_question_row_by_key(questions, missing_fields[0])
        if matched_row is not None:
            mapped = map_question_to_model(matched_row)
            return IntakeSessionFirstQuestion(
                key=mapped.key,
                text=question_text,
                type=mapped.type,
                options=mapped.options,
            )
        return IntakeSessionFirstQuestion(
            key="llm_followup",
            text=question_text,
            type="text",
            options=None,
        )

    if isinstance(suggested_key, str):
        matched_row = find_question_row_by_key(questions, suggested_key)
        if matched_row is not None:
            return map_question_to_model(matched_row)

    for row in questions:
        question_key = row.get("key")
        if isinstance(question_key, str) and question_key in missing_fields:
            return map_question_to_model(row)
    return None


resolve_next_intake_question = choose_next_intake_question
