"""Questionnaire ordering helpers for intake sessions."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import HTTPException, status

from app.schemas.intake_sessions import IntakeSessionFirstQuestion


def map_question_to_model(question: dict) -> IntakeSessionFirstQuestion:
    """Map a PostgREST ``questions`` row into ``IntakeSessionFirstQuestion``."""
    try:
        qid = question.get("id")
        qtext = question.get("text")
        qtype = question.get("type")
        qid_uuid = qid if isinstance(qid, UUID) else UUID(str(qid))
        if not isinstance(qtext, str) or not isinstance(qtype, str):
            raise ValueError("Invalid question fields")
        return IntakeSessionFirstQuestion(id=qid_uuid, text=qtext, type=qtype)
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected response from Supabase when loading question definition.",
        ) from exc


def has_answer_value(value: Any) -> bool:
    """Whether ``value`` counts as an answered field for progress tracking."""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict, set)):
        return len(value) > 0
    return True


def merge_intake_criteria_dict(existing: object, incoming: object) -> dict[str, Any]:
    """Shallow-merge answer payloads into prior ``criteria`` (both must be dict-like)."""
    base: dict[str, Any] = existing if isinstance(existing, dict) else {}
    inc: dict[str, Any] = incoming if isinstance(incoming, dict) else {}
    return {**base, **inc}


def max_answered_order_for_keys(questions: list[dict], criteria: dict[str, Any]) -> int:
    """Largest ``order_index`` among questions whose ``key`` has a non-empty value in ``criteria``."""
    best = -1
    for q in questions:
        k = q.get("key")
        if not isinstance(k, str) or not k:
            continue
        if k not in criteria:
            continue
        if not has_answer_value(criteria[k]):
            continue
        try:
            o = int(q["order_index"])
        except (TypeError, ValueError):
            continue
        best = max(best, o)
    return best


def order_for_question_id(questions: list[dict], question_id: UUID) -> int | None:
    sid = str(question_id)
    for q in questions:
        qid = q.get("id")
        if qid is not None and str(qid) == sid:
            try:
                return int(q["order_index"])
            except (TypeError, ValueError):
                return None
    return None


def _order_key(row: dict) -> int:
    try:
        return int(row["order_index"])
    except (KeyError, TypeError, ValueError):
        return 0


def next_question_row_after_order(questions: list[dict], *, after_order: int) -> dict | None:
    """First question with ``order_index`` strictly greater than ``after_order``."""
    ordered = sorted(questions, key=_order_key)
    for q in ordered:
        try:
            o = int(q["order_index"])
        except (TypeError, ValueError):
            continue
        if o > after_order:
            return q
    return None
