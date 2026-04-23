"""``public.intake_sessions`` (Supabase)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.core.db_safe import execute_db_safe
from app.core.deps import CurrentUser, SupabaseSdkDep
from app.models.intake_sessions import IntakeSession
from app.schemas.intake_sessions import (
    CreateIntakeSessionResponse,
    SubmitIntakeSessionAnswersRequest,
    SubmitIntakeSessionAnswersResponse,
)
from app.utils.intake_questions import (
    append_intake_criteria_answer,
    load_first_intake_question,
    load_intake_questions,
    map_question_to_model,
    next_question_row_after_order,
    order_for_question_key,
)
from app.utils.intake_rows import (
    load_intake_session_row,
    parse_intake_session,
)
from app.utils.search_profiles import create_search_profile, ensure_search_profile_access
from app.utils.supabase_response import expect_single_row_from_result

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
    session_result = await execute_db_safe(
        client.table("intake_sessions")
        .insert({"search_profile_id": None, "criteria": {}})
        .execute(),
    )
    session_row = expect_single_row_from_result(
        session_result,
        detail="Unexpected response from Supabase when creating intake session.",
    )
    session = parse_intake_session(session_row)
    first_question = await load_first_intake_question(client)

    if session.id is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected response from Supabase when creating intake session.",
        )

    return CreateIntakeSessionResponse(
        session_id=session.id,
        status=session.status,
        first_question=first_question,
    )


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
    session_row = await load_intake_session_row(client, session_id)
    await ensure_search_profile_access(
        client,
        session_row.get("search_profile_id"),
        current_user.id,
    )
    return parse_intake_session(session_row)


@router.patch(
    "/intake-sessions/{session_id}/answers",
    response_model=SubmitIntakeSessionAnswersResponse,
)
async def submit_intake_session_answers(
    session_id: UUID,
    body: SubmitIntakeSessionAnswersRequest,
    client: SupabaseSdkDep,
) -> SubmitIntakeSessionAnswersResponse:
    answer_key = body.key.strip()
    session_row = await load_intake_session_row(client, session_id)
    questions = await load_intake_questions(client)

    merged_criteria = append_intake_criteria_answer(
        session_row.get("criteria"),
        answer_key,
        body.answers,
    )

    answered_order = order_for_question_key(questions, answer_key)
    if answered_order is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unknown question key for this questionnaire.",
        )

    next_row = next_question_row_after_order(questions, after_order=answered_order)
    next_question = map_question_to_model(next_row) if next_row is not None else None

    result = await execute_db_safe(
        client.table("intake_sessions")
        .update({"criteria": merged_criteria, "status": "in_progress"})
        .eq("id", str(session_id))
        .execute(),
    )
    row = expect_single_row_from_result(
        result,
        detail="Unexpected response from Supabase when submitting intake session answers.",
    )
    return SubmitIntakeSessionAnswersResponse(
        session=parse_intake_session(row),
        next_question=next_question,
    )


@router.post(
    "/intake-sessions/{session_id}/complete",
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

    session_update = await execute_db_safe(
        client.table("intake_sessions")
        .update({"status": "completed", "search_profile_id": search_profile_id})
        .eq("id", str(session_id))
        .execute(),
    )
    updated_row = expect_single_row_from_result(
        session_update,
        detail="Unexpected response from Supabase when completing intake session.",
    )
    return parse_intake_session(updated_row)
