"""Validation helpers for intake-related payload fragments."""

from __future__ import annotations


def _has_answer(value: object) -> bool:
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
        if _has_answer(criteria.get(question_key)):
            count += 1
    return count
