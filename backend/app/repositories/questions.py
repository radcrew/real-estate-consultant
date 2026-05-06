"""Persistence and questionnaire helpers for ``public.questions`` (Supabase)."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from supabase import AsyncClient

from app.core.db_safe import execute_db_safe
from app.schemas.intake_sessions import IntakeSessionFirstQuestion
from app.utils.supabase_response import as_row_list, get_single_row

_FIRST_QUESTION_SELECT = "key, title, text, type, options, required"
_QUESTION_SELECT = "key, title, text, type, options, order_index, required"
_LOAD_QUESTIONS_ERROR = "No question is configured for intake flow."

# ``questions.type`` values that use a numeric range and optional ``options.unit``.
_RANGE_QUESTION_TYPES: frozenset[str] = frozenset(
    {"range", "numeric_range", "sqft_range", "rent_range", "size_range"},
)


def _range_unit_from_options(qtype: str, options: Any) -> str | None:
    """Return ``options["unit"]`` when ``qtype`` is a range style and unit is present."""
    t = qtype.strip().lower() if isinstance(qtype, str) else ""
    if t not in _RANGE_QUESTION_TYPES:
        return None
    if isinstance(options, dict):
        raw = options.get("unit")
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    return None


def map_question_to_model(question: dict) -> IntakeSessionFirstQuestion:
    """Map a PostgREST ``questions`` row into ``IntakeSessionFirstQuestion``."""
    try:
        qkey = question.get("key")
        qtitle = question.get("title")
        qtext = question.get("text")
        qtype = question.get("type")
        qoptions = question.get("options")
        if not isinstance(qkey, str) or not qkey.strip():
            raise ValueError("Invalid question key")
        if not isinstance(qtext, str) or not isinstance(qtype, str):
            raise ValueError("Invalid question fields")
        title = qtitle.strip() if isinstance(qtitle, str) else ""
        return IntakeSessionFirstQuestion(
            key=qkey.strip(),
            title=title,
            text=qtext,
            type=qtype,
            options=qoptions,
        )
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


def sorted_intake_questions(questions: list[dict]) -> list[dict]:
    """Return questionnaire rows ordered by ``order_index`` (stable for prompts and UI)."""
    return sorted(questions, key=_order_key)


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
    row = get_single_row(result, detail=_LOAD_QUESTIONS_ERROR)
    return map_question_to_model(row)


async def load_intake_question_filters(client: AsyncClient) -> dict[str, dict[str, str]]:
    """Build ``{ question.key: {\"type\", \"label\"} }`` from ``questions`` for UI filters."""
    result = await execute_db_safe(
        client.table("questions").select("key, type, title").order("order_index").execute(),
    )
    rows = as_row_list(result.data)
    out: dict[str, dict[str, str]] = {}
    for row in rows:
        raw_key = row.get("key")
        if not isinstance(raw_key, str) or not raw_key.strip():
            continue
        k = raw_key.strip()
        qtype = row.get("type")
        qtitle = row.get("title")
        type_str = qtype.strip() if isinstance(qtype, str) and qtype.strip() else "text"
        label_str = qtitle.strip() if isinstance(qtitle, str) else ""
        out[k] = {"type": type_str, "label": label_str}
    return out


async def load_question_key_metadata(
    client: AsyncClient,
) -> tuple[dict[str, str], dict[str, str], dict[str, str | None]]:
    """Map each question ``key`` to ``(type, title, unit)`` for search / display APIs.

    ``unit`` is set from ``questions.options->unit`` only for range-style ``type`` values.
    """
    result = await execute_db_safe(
        client.table("questions")
        .select("key, type, title, options")
        .order("order_index")
        .execute(),
    )
    rows = as_row_list(result.data)
    types: dict[str, str] = {}
    titles: dict[str, str] = {}
    units: dict[str, str | None] = {}
    for row in rows:
        key = row.get("key")
        if not isinstance(key, str) or not key.strip():
            continue
        types[key] = row.get("type")
        titles[key] = row.get("title")
        units[key] = _range_unit_from_options(row.get("type"), row.get("options"))
    return types, titles, units


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
    return get_single_row(
        result,
        detail="Unexpected response from Supabase when creating question.",
    )
