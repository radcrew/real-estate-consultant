"""``public.intake_sessions`` (Supabase)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.core.db_safe import execute_db_safe
from app.core.deps import CurrentUser, SupabaseSdkDep
from app.models.intake_sessions import IntakeSession
from app.schemas.intake_sessions import CreateIntakeSessionRequest, PatchIntakeSessionStatusRequest

router = APIRouter(tags=["intake-sessions"])


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
    search_profile_id = body.search_profile_id
    if search_profile_id is None:
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
        if not isinstance(sid, str):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unexpected response from Supabase when creating search profile for intake.",
            )
        search_profile_id = UUID(sid)
    else:
        owned = await execute_db_safe(
            client.table("search_profiles")
            .select("id")
            .eq("id", str(search_profile_id))
            .eq("user_id", str(current_user.id))
            .limit(1)
            .execute(),
        )
        raw = owned.data
        rows = raw if isinstance(raw, list) else []
        if len(rows) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Search profile not found.",
            )

    payload = body.model_dump(mode="json", exclude_none=True)
    payload["search_profile_id"] = str(search_profile_id)
    result = await execute_db_safe(client.table("intake_sessions").insert(payload).execute())
    row = _expect_one_row(
        result.data,
        detail="Unexpected response from Supabase when creating intake session.",
    )
    return IntakeSession.model_validate(row)


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
