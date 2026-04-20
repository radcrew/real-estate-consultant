"""``public.intake_sessions`` (Supabase)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.core.db_safe import execute_db_safe
from app.core.deps import CurrentUser, SupabaseSdkDep
from app.models.intake_sessions import IntakeSession
from app.schemas.intake_sessions import CreateIntakeSessionRequest, PatchIntakeSessionStatusRequest

router = APIRouter(tags=["intake-sessions"])


def _as_row_list(raw: object) -> list[dict]:
    if isinstance(raw, list):
        return [r for r in raw if isinstance(r, dict)]
    if isinstance(raw, dict):
        return [raw]
    return []


_INTAKE_SESSION_SELECT = (
    "id, status, created_at, search_profile_id, criteria, search_profiles!inner(user_id)"
)


def _intake_session_row_for_response(row: dict) -> dict:
    """Drop embedded join payload; only ``intake_sessions`` columns are exposed."""
    return {k: v for k, v in row.items() if k != "search_profiles"}


def _expect_one_row(raw: object, *, detail: str) -> dict:
    if isinstance(raw, list):
        if len(raw) != 1:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)
        row = raw[0]
    elif isinstance(raw, dict):
        row = raw
    else:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)
    if not isinstance(row, dict):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)
    return row


@router.post(
    "/intake-sessions",
    status_code=status.HTTP_201_CREATED,
    response_model=IntakeSession,
)
async def create_intake_session(
    body: CreateIntakeSessionRequest,
    client: SupabaseSdkDep,
    current_user: CurrentUser,
) -> IntakeSession:
    profile_result = await execute_db_safe(
        client.table("search_profiles")
        .insert({"user_id": str(current_user.id)})
        .execute(),
    )
    profile_row = _expect_one_row(
        profile_result.data,
        detail="Unexpected response from Supabase when creating search profile for intake.",
    )
    sid = profile_row.get("id")
    if isinstance(sid, str):
        search_profile_id = UUID(sid)
    elif isinstance(sid, UUID):
        search_profile_id = sid
    else:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected response from Supabase when creating search profile for intake.",
        )

    payload = body.model_dump(mode="json", exclude_none=True)
    payload["search_profile_id"] = str(search_profile_id)
    result = await execute_db_safe(client.table("intake_sessions").insert(payload).execute())
    row = _expect_one_row(
        result.data,
        detail="Unexpected response from Supabase when creating intake session.",
    )
    return IntakeSession.model_validate(row)


@router.get(
    "/intake-sessions",
    response_model=list[IntakeSession],
)
async def list_intake_sessions(
    client: SupabaseSdkDep,
    current_user: CurrentUser,
) -> list[IntakeSession]:
    """Return intake sessions whose linked search profile belongs to the caller only."""
    sessions = await execute_db_safe(
        client.table("intake_sessions")
        .select(_INTAKE_SESSION_SELECT)
        .eq("search_profiles.user_id", str(current_user.id))
        .order("created_at", desc=True)
        .execute(),
    )
    return [
        IntakeSession.model_validate(_intake_session_row_for_response(r))
        for r in _as_row_list(sessions.data)
    ]


@router.get(
    "/intake-sessions/{session_id}",
    response_model=IntakeSession,
)
async def get_intake_session(
    session_id: UUID,
    client: SupabaseSdkDep,
    current_user: CurrentUser,
) -> IntakeSession:
    """Return one session only if its linked search profile belongs to the caller."""
    result = await execute_db_safe(
        client.table("intake_sessions")
        .select(_INTAKE_SESSION_SELECT)
        .eq("id", str(session_id))
        .eq("search_profiles.user_id", str(current_user.id))
        .limit(1)
        .execute(),
    )
    rows = _as_row_list(result.data)
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intake session not found.",
        )
    return IntakeSession.model_validate(_intake_session_row_for_response(rows[0]))


@router.patch(
    "/intake-sessions/{session_id}",
    response_model=IntakeSession,
)
async def patch_intake_session_status(
    session_id: UUID,
    body: PatchIntakeSessionStatusRequest,
    client: SupabaseSdkDep,
) -> IntakeSession:
    result = await execute_db_safe(
        client.table("intake_sessions")
        .update({"status": body.status})
        .eq("id", str(session_id))
        .execute(),
    )
    raw = result.data
    if isinstance(raw, list) and len(raw) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intake session not found.",
        )
    row = _expect_one_row(
        raw,
        detail="Unexpected response from Supabase when updating intake session.",
    )
    return IntakeSession.model_validate(row)
