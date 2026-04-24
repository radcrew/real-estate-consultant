"""``public.intake_sessions`` (Supabase)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.core.deps import CurrentUser, SupabaseSdkDep
from app.models.intake_sessions import IntakeSession
from app.repositories.intake_sessions import (
    append_intake_criteria_answer,
    create_intake_session_row,
    load_intake_session_row,
    parse_intake_session,
    update_intake_session_after_answers,
    update_intake_session_completed,
)
from app.repositories.questions import (
    load_first_intake_question,
    load_intake_questions,
    map_question_to_model,
    next_question_row_after_order,
    order_for_question_key,
)
from app.repositories.search_profiles import (
    create_search_profile,
    ensure_search_profile_access,
)
from app.schemas.intake_sessions import (
    CreateIntakeSessionResponse,
    UpdateIntakeSessionAnswersRequest,
    UpdateIntakeSessionAnswersResponse,
)
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
    
    created_session = await create_intake_session_row(client)
    
    validated_session = parse_intake_session(created_session)
    
    first_question = await load_first_intake_question(client)

    if validated_session.id is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected response from Supabase when creating intake session.",
        )

    return CreateIntakeSessionResponse(
        session_id=validated_session.id,
        status=validated_session.status,
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
    response_model=UpdateIntakeSessionAnswersResponse,
)
async def submit_intake_session_answers(
    session_id: UUID,
    body: UpdateIntakeSessionAnswersRequest,
    client: SupabaseSdkDep,
) -> UpdateIntakeSessionAnswersResponse:
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

    row = await update_intake_session_after_answers(
        client,
        session_id,
        merged_criteria,
    )
    return UpdateIntakeSessionAnswersResponse(
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

    updated_row = await update_intake_session_completed(
        client,
        session_id,
        search_profile_id,
    )
    return parse_intake_session(updated_row)
