"""Persistence and questionnaire helpers for ``public.questions`` (Supabase)."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from supabase import AsyncClient

from app.core.db_safe import execute_db_safe
from app.schemas.intake_sessions import IntakeSessionFirstQuestion
from app.utils.supabase_response import as_row_list, expect_single_row_from_result

_FIRST_QUESTION_SELECT = "key, text, type"
_QUESTION_SELECT = "key, text, type, order_index"
_LOAD_QUESTIONS_ERROR = "No question is configured for intake flow."


def map_question_to_model(question: dict) -> IntakeSessionFirstQuestion:
    """Map a PostgREST ``questions`` row into ``IntakeSessionFirstQuestion``."""
    try:
        qkey = question.get("key")
        qtext = question.get("text")
        qtype = question.get("type")
        if not isinstance(qkey, str) or not qkey.strip():
            raise ValueError("Invalid question key")
        if not isinstance(qtext, str) or not isinstance(qtype, str):
            raise ValueError("Invalid question fields")
        return IntakeSessionFirstQuestion(key=qkey.strip(), text=qtext, type=qtype)
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected response from Supabase when loading question definition.",
        ) from exc


def order_for_question_key(questions: list[dict], key: str) -> int | None:
    """Return ``order_index`` for the question row with this ``key``, if any."""
    for q in questions:
        k = q.get("key")
        if isinstance(k, str) and k == key:
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


async def load_first_intake_question(client: AsyncClient) -> IntakeSessionFirstQuestion:
    result = await execute_db_safe(
        client.table("questions")
        .select(_FIRST_QUESTION_SELECT)
        .order("order_index")
        .limit(1)
        .execute(),
    )
    row = expect_single_row_from_result(result, detail=_LOAD_QUESTIONS_ERROR)
    return map_question_to_model(row)


async def load_intake_questions(client: AsyncClient) -> list[dict[str, Any]]:
    result = await execute_db_safe(
        client.table("questions")
        .select(_QUESTION_SELECT)
        .order("order_index")
        .execute(),
    )
    questions = as_row_list(result.data)
    if not questions:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=_LOAD_QUESTIONS_ERROR,
        )
    return questions


async def insert_question_row(client: AsyncClient, payload: dict[str, Any]) -> dict[str, Any]:
    result = await execute_db_safe(client.table("questions").insert(payload).execute())
    return expect_single_row_from_result(
        result,
        detail="Unexpected response from Supabase when creating question.",
    )
