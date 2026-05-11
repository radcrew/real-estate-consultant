"""``public.intake_sessions`` (Supabase)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.core.deps import CurrentUser, SupabaseSdkDep
from app.models.intake_sessions import IntakeSession
from app.repositories.intake_sessions import (
    load_intake_session_row,
    parse_intake_session,
    update_intake_session_completed,
)
from app.repositories.search_profiles import (
    create_search_profile,
    ensure_search_profile_access,
)

router = APIRouter()


@router.post(
    "/{session_id}/complete",
    response_model=IntakeSession,
)
async def complete_intake_session(
    session_id: UUID,
    client: SupabaseSdkDep,
    current_user: CurrentUser,
) -> IntakeSession:
    session_row = await load_intake_session_row(client, session_id)
    search_profile_id = await ensure_search_profile_access(
        client,
        session_row.get("search_profile_id"),
        current_user.id,
    )
    if search_profile_id is None:
        search_profile_id = await create_search_profile(client, current_user.id)

    updated_row = await update_intake_session_completed(
        client,
        session_id,
        search_profile_id,
    )
    return parse_intake_session(updated_row)
