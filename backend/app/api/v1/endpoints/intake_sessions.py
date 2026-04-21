"""``public.intake_sessions`` (Supabase)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.core.db_safe import execute_db_safe
from app.core.deps import CurrentUser, SupabaseSdkDep
from app.models.intake_sessions import IntakeSession
from app.schemas.intake_sessions import (
    CreateIntakeSessionResponse,
    IntakeSessionFirstQuestion,
    SubmitIntakeSessionAnswersRequest,
)
from app.utils.intake_criteria import normalize_intake_criteria
from app.utils.intake_rows import strip_intake_session_row
from app.utils.supabase_response import as_row_list, require_single_row

router = APIRouter(tags=["intake-sessions"])


@router.post(
    "/intake-sessions",
    status_code=status.HTTP_201_CREATED,
    response_model=CreateIntakeSessionResponse,
)
async def create_intake_session(
    client: SupabaseSdkDep,
) -> CreateIntakeSessionResponse:
    """Create an intake session and return first question."""
    # Force nullable FK to null on creation. Some environments may still have an
    # old DB default (gen_random_uuid) that would violate FK to search_profiles.
    result = await execute_db_safe(
        client.table("intake_sessions").insert({"search_profile_id": None}).execute(),
    )
    row = require_single_row(
        result.data,
        detail="Unexpected response from Supabase when creating intake session.",
    )
    session = IntakeSession.model_validate(row)

    question = require_single_row(
        (
            await execute_db_safe(
                client.table("questions")
                .select("id, text, type")
                .order("order_index")
                .limit(1)
                .execute()
            )
        ).data,
        detail="No question is configured for intake flow.",
    )

    qid, qtext, qtype = (
        question.get("id"),
        question.get("text"),
        question.get("type"),
    )

    if not isinstance(qid, str) or not isinstance(qtext, str) or not isinstance(qtype, str):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected response from Supabase when loading first question.",
        )

    if session.id is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected response from Supabase when creating intake session.",
        )

    return CreateIntakeSessionResponse(
        session_id=session.id,
        status=session.status,
        first_question=IntakeSessionFirstQuestion(id=UUID(qid), text=qtext, type=qtype),
    )


@router.get(
    "/intake-sessions",
    response_model=list[IntakeSession],
)
async def list_intake_sessions(
    client: SupabaseSdkDep,
    current_user: CurrentUser,
) -> list[IntakeSession]:
    """Return intake sessions whose linked search profile belongs to the caller."""
    sessions = await execute_db_safe(
        client.table("intake_sessions")
        .select("id, status, created_at, search_profile_id, criteria")
        .eq("search_profiles.user_id", str(current_user.id))
        .order("created_at", desc=True)
        .execute(),
    )
    return [
        IntakeSession.model_validate(strip_intake_session_row(r))
        for r in as_row_list(sessions.data)
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
        .select("id, status, created_at, search_profile_id, criteria")
        .eq("id", str(session_id))
        .limit(1)
        .execute(),
    )
    rows = as_row_list(result.data)
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intake session not found.",
        )
    return IntakeSession.model_validate(strip_intake_session_row(rows[0]))


@router.patch(
    "/intake-sessions/{session_id}/answers",
    response_model=IntakeSession,
)
async def submit_intake_session_answers(
    session_id: UUID,
    body: SubmitIntakeSessionAnswersRequest,
    client: SupabaseSdkDep,
) -> IntakeSession:
    result = await execute_db_safe(
        client.table("intake_sessions")
        .update({"criteria": body.answers, "status": body.status})
        .eq("id", str(session_id))
        .execute(),
    )
    raw = result.data
    if isinstance(raw, list) and len(raw) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intake session not found.",
        )
    row = require_single_row(
        raw,
        detail="Unexpected response from Supabase when submitting intake session answers.",
    )
    return IntakeSession.model_validate(row)


@router.post(
    "/intake-sessions/{session_id}/complete",
    response_model=IntakeSession,
)
async def complete_intake_session(
    session_id: UUID,
    client: SupabaseSdkDep,
    current_user: CurrentUser,
) -> IntakeSession:
    session_result = await execute_db_safe(
        client.table("intake_sessions").select("*").eq("id", str(session_id)).limit(1).execute(),
    )
    session_row = require_single_row(
        session_result.data,
        detail="Unexpected response from Supabase when loading intake session.",
    )

    normalized_filters = normalize_intake_criteria(session_row.get("criteria"))
    existing_profile_id = session_row.get("search_profile_id")
    if existing_profile_id is not None:
        owned_profile = await execute_db_safe(
            client.table("search_profiles")
            .select("id")
            .eq("id", str(existing_profile_id))
            .eq("user_id", str(current_user.id))
            .limit(1)
            .execute(),
        )
        if not as_row_list(owned_profile.data):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Intake session not found.",
            )
        search_profile_id = str(existing_profile_id)
        await execute_db_safe(
            client.table("search_profiles")
            .update({"filters": normalized_filters})
            .eq("id", search_profile_id)
            .execute(),
        )
    else:
        profile_result = await execute_db_safe(
            client.table("search_profiles")
            .insert({"user_id": str(current_user.id), "filters": normalized_filters})
            .execute(),
        )
        profile_row = require_single_row(
            profile_result.data,
            detail="Unexpected response from Supabase when creating search profile.",
        )
        profile_id = profile_row.get("id")
        if not isinstance(profile_id, str):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unexpected response from Supabase when creating search profile.",
            )
        search_profile_id = profile_id

    session_update = await execute_db_safe(
        client.table("intake_sessions")
        .update({"status": "completed", "search_profile_id": search_profile_id})
        .eq("id", str(session_id))
        .execute(),
    )
    updated_row = require_single_row(
        session_update.data,
        detail="Unexpected response from Supabase when completing intake session.",
    )
    return IntakeSession.model_validate(updated_row)


