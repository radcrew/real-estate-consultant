"""Validation helpers for intake-related payload fragments."""

from __future__ import annotations

from typing import Any


def has_answer(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) > 0
    return True


def compute_current_index(questions: list[dict], criteria: object) -> int:
    """Count how many configured question keys are already answered in criteria."""
    if not questions or not isinstance(criteria, dict):
        return 0

    count = 0
    for row in questions:
        question_key = row.get("key")
        if not isinstance(question_key, str):
            continue
        if has_answer(criteria.get(question_key)):
            count += 1
    return count


def _missing_required_fields(
    merged_criteria: dict[str, Any],
    required_fields: list[str],
    skipped_fields: set[str],
) -> list[str]:
    return [
        key
        for key in required_fields
        if key not in merged_criteria and key not in skipped_fields
    ]


def merge_missing_fields(
    *,
    merged_criteria: dict[str, Any],
    required_fields: list[str],
    model_missing: list[str],
    skipped_fields: list[str] | None = None,
) -> list[str]:
    """Use the model's missing keys when they match real gaps; otherwise criteria-based gaps."""
    skipped = set(skipped_fields or [])
    still_missing = _missing_required_fields(merged_criteria, required_fields, skipped)
    from_model = [key for key in model_missing if key in required_fields and key not in skipped]
    if from_model:
        overlap = [key for key in from_model if key in still_missing]
        return overlap if overlap else still_missing
    return still_missing
