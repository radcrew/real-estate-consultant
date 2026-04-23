"""Row shaping and loading for ``intake_sessions`` PostgREST responses."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from supabase import AsyncClient

from app.core.db_safe import execute_db_safe
from app.models.intake_sessions import IntakeSession
from app.utils.supabase_response import as_row_list, expect_single_row_from_result

INTAKE_SESSION_EMBEDDED_RELATION_KEYS: frozenset[str] = frozenset({"search_profiles"})

_INTAKE_SESSION_SELECT = "id, status, created_at, search_profile_id, criteria"
_LOAD_SESSION_ERROR = "Unexpected response from Supabase when loading intake session."


def intake_session_not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Intake session not found.",
    )


def parse_intake_session(row: dict[str, Any]) -> IntakeSession:
    return IntakeSession.model_validate(strip_intake_session_row(row))


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
    return expect_single_row_from_result(result, detail=_LOAD_SESSION_ERROR)


def strip_intake_session_row(
    row: dict,
    *,
    extra_embedded_keys: frozenset[str] | None = None,
) -> dict:
    """Remove nested relation keys from a joined select (e.g. ``search_profiles``)."""
    excluded = INTAKE_SESSION_EMBEDDED_RELATION_KEYS | (extra_embedded_keys or frozenset())
    return {k: v for k, v in row.items() if k not in excluded}
