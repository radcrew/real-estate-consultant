"""``public.intake_sessions`` (Supabase)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.core.db_safe import execute_db_safe
from app.core.deps import SupabaseSdkDep
from app.models.intake_sessions import IntakeSession
from app.schemas.intake_sessions import CreateIntakeSessionRequest

router = APIRouter(tags=["intake-sessions"])


def _single_row_from_insert(raw: object) -> dict:
    if isinstance(raw, list):
        if len(raw) != 1:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unexpected response from Supabase when creating intake session.",
            )
        row = raw[0]
    elif isinstance(raw, dict):
        row = raw
    else:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected response from Supabase when creating intake session.",
        )
    if not isinstance(row, dict):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected response from Supabase when creating intake session.",
        )
    return row


@router.post(
    "/intake-sessions",
    status_code=status.HTTP_201_CREATED,
    response_model=IntakeSession,
)
async def create_intake_session(
    body: CreateIntakeSessionRequest,
    client: SupabaseSdkDep,
) -> IntakeSession:
    payload = body.model_dump(mode="json", exclude_none=True)
    result = await execute_db_safe(client.table("intake_sessions").insert(payload).execute())
    row = _single_row_from_insert(result.data)
    return IntakeSession.model_validate(row)
