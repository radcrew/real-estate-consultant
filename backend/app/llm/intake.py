"""LLM-specific helpers for the intake flow."""

from __future__ import annotations

from app.repositories.questions import map_question_to_model
from app.schemas.intake_sessions import IntakeSessionFirstQuestion

INTAKE_OPENING_MESSAGE = (
    "Hi! I'm here to help you find the right commercial property. "
    "Tell me what you're looking for — be as detailed or brief as you want. "
    'For example: "I need a 100k sqft industrial warehouse with 32ft clear '
    'height in Chicago for lease, with at least 20 dock doors."'
)


def _find_question_row(questions: list[dict], question_key: str) -> dict | None:
    for row in questions:
        if row.get("key") == question_key:
            return row
    return None


def select_next_question(
    questions: list[dict],
    proposed_next: object,
    missing_fields: list[str],
) -> IntakeSessionFirstQuestion | None:
    """Prefer LLM-authored ``text``; bind to a real question row when possible."""
    if not isinstance(proposed_next, dict):
        proposed_next = {}
    proposed_key = proposed_next.get("key")
    proposed_text = proposed_next.get("text")

    if isinstance(proposed_text, str) and proposed_text.strip():
        text = proposed_text.strip()
        base_row = _find_question_row(questions, proposed_key) if isinstance(proposed_key, str) else None
        if base_row is None and missing_fields:
            base_row = _find_question_row(questions, missing_fields[0])
        if base_row is not None:
            mapped = map_question_to_model(base_row)
            return IntakeSessionFirstQuestion(
                key=mapped.key,
                text=text,
                type=mapped.type,
                options=mapped.options,
            )
        return IntakeSessionFirstQuestion(
            key="llm_followup",
            text=text,
            type="text",
            options=None,
        )

    if isinstance(proposed_key, str):
        question_row = _find_question_row(questions, proposed_key)
        if question_row is not None:
            return map_question_to_model(question_row)

    for row in questions:
        question_key = row.get("key")
        if isinstance(question_key, str) and question_key in missing_fields:
            return map_question_to_model(row)
    return None
