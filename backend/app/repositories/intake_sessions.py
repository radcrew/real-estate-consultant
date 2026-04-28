"""Persistence and intake-session row handling for ``public.intake_sessions`` (Supabase)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from supabase import AsyncClient

from app.core.db_safe import execute_db_safe
from app.models.intake_sessions import IntakeSession
from app.utils.supabase_response import as_row_list, get_single_row
from app.utils.values import clean_str_or_none, try_float

INTAKE_SESSION_EMBEDDED_RELATION_KEYS: frozenset[str] = frozenset({"search_profiles"})

_INTAKE_SESSION_SELECT = "id, status, created_at, search_profile_id, criteria"
_LOAD_SESSION_ERROR = "Unexpected response from Supabase when loading intake session."


def intake_session_not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Intake session not found.",
    )


def strip_intake_session_row(
    row: dict,
    *,
    extra_embedded_keys: frozenset[str] | None = None,
) -> dict:
    """Remove nested relation keys from a joined select (e.g. ``search_profiles``)."""
    excluded = INTAKE_SESSION_EMBEDDED_RELATION_KEYS | (extra_embedded_keys or frozenset())
    return {k: v for k, v in row.items() if k not in excluded}


def parse_intake_session(row: dict[str, Any]) -> IntakeSession:
    return IntakeSession.model_validate(strip_intake_session_row(row))


def append_intake_criteria_answer(
    previous_criteria: object,
    question_key: str,
    answers: Any,
) -> dict[str, Any]:
    """Return prior criteria with ``{question_key: answers}`` applied (shallow copy)."""
    base: dict[str, Any] = previous_criteria if isinstance(previous_criteria, dict) else {}
    key = question_key.strip()
    return {**base, key: answers}


async def load_intake_session_row(client: AsyncClient, session_id: UUID) -> dict[str, Any]:
    result = await execute_db_safe(
        client.table("intake_sessions")
        .select(_INTAKE_SESSION_SELECT)
        .eq("id", str(session_id))
        .limit(1)
        .execute(),
    )
    if not as_row_list(result.data):
        raise intake_session_not_found()
    return get_single_row(result, detail=_LOAD_SESSION_ERROR)


async def create_intake_session_row(client: AsyncClient) -> dict[str, Any]:
    result = await execute_db_safe(
        client.table("intake_sessions")
        .insert({"search_profile_id": None, "criteria": {}})
        .execute(),
    )
    return get_single_row(
        result,
        detail="Unexpected response from Supabase when creating intake session.",
    )


async def save_intake_criteria(
    client: AsyncClient,
    session_id: UUID,
    merged_criteria: dict[str, Any],
) -> dict[str, Any]:
    result = await execute_db_safe(
        client.table("intake_sessions")
        .update({"criteria": merged_criteria, "status": "in_progress"})
        .eq("id", str(session_id))
        .execute(),
    )
    return get_single_row(
        result,
        detail="Unexpected response from Supabase when submitting intake session answers.",
    )


async def update_intake_session_completed(
    client: AsyncClient,
    session_id: UUID,
    search_profile_id: str,
) -> dict[str, Any]:
    result = await execute_db_safe(
        client.table("intake_sessions")
        .update({"status": "completed", "search_profile_id": search_profile_id})
        .eq("id", str(session_id))
        .execute(),
    )
    return get_single_row(
        result,
        detail="Unexpected response from Supabase when completing intake session.",
    )
