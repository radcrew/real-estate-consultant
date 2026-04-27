"""LLM-specific helpers for the intake flow."""

from __future__ import annotations

from app.repositories.questions import map_question_to_model
from app.schemas.intake_sessions import IntakeSessionFirstQuestion

LLM_INTAKE_OPENING_MESSAGE = (
    "Hi! I'm here to help you find the right commercial property. "
    "Tell me what you're looking for â€” be as detailed or brief as you want. "
    'For example: "I need a 100k sqft industrial warehouse with 32ft clear '
    'height in Chicago for lease, with at least 20 dock doors."'
)

REQUIRED_LLM_FIELDS: tuple[str, ...] = (
    "building_type",
    "location",
    "radius_miles",
    "listing_type",
)


def next_question_from_llm_response(
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
        base_row = None
        if isinstance(proposed_key, str):
            for row in questions:
                if row.get("key") == proposed_key:
                    base_row = row
                    break
        if base_row is None and missing_fields:
            missing_key = missing_fields[0]
            for row in questions:
                if row.get("key") == missing_key:
                    base_row = row
                    break
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
        for row in questions:
            if row.get("key") == proposed_key:
                return map_question_to_model(row)

    for row in questions:
        question_key = row.get("key")
        if isinstance(question_key, str) and question_key in missing_fields:
            return map_question_to_model(row)
    return None
