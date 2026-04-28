"""``public.intake_sessions`` (Supabase)."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import CurrentUser, SupabaseSdkDep
from app.llm.huggingface import (
    generate_llm_opening_question_text,
    parse_intake_with_huggingface,
)
from app.llm.intake import next_question_from_llm_response
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
    CreateIntakeSessionResponseGuided,
    CreateIntakeSessionResponseLlm,
    LlmExtractedIntakePayload,
    IntakeSessionFirstQuestion,
    SubmitLlmIntakeInputRequest,
    SubmitLlmIntakeInputResponse,
    UpdateIntakeSessionAnswersRequest,
    UpdateIntakeSessionAnswersResponse,
)
LLM_INTAKE_OPENING_MESSAGE = (
    "Hi! I'm here to help you find the right commercial property. "
    "Tell me what you're looking for — be as detailed or brief as you want. "
    'For example: "I need a 100k sqft industrial warehouse with 32ft clear '
    'height in Chicago for lease, with at least 20 dock doors."'
)

router = APIRouter(tags=["intake-sessions"])

_REQUIRED_LLM_FIELDS: tuple[str, ...] = ("building_type", "location", "radius_miles", "listing_type")


def _has_answer(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) > 0
    return True


def _current_index_for_answered_count(questions: list[dict], criteria: object) -> int:
    if not questions or not isinstance(criteria, dict):
        return 0
    count = 0
    for row in questions:
        qkey = row.get("key")
        if not isinstance(qkey, str):
            continue
        if _has_answer(criteria.get(qkey)):
            count += 1
    return count


@router.post(
    "/intake-sessions",
    status_code=status.HTTP_201_CREATED,
    response_model=CreateIntakeSessionResponse,
)
async def create_intake_session(
    client: SupabaseSdkDep,
    mode: Literal["llm", "guided"] = Query(
        "guided",
        description='Intake style: "guided" uses the questionnaire; "llm" returns an open prompt.',
    ),
) -> CreateIntakeSessionResponse:
    """Create an intake session. Guided mode returns the first question; LLM mode returns a welcome message."""
    created_session = await create_intake_session_row(client)
    questions = await load_intake_questions(client)
    total_questions = len(questions)
    
    if not questions:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No questions configured for intake flow.",
        )

    first_question = map_question_to_model(questions[0])


    if mode == "llm":
        try:
            llm_question_text = await generate_llm_opening_question_text(
                welcome_message=LLM_INTAKE_OPENING_MESSAGE,
                question_key=first_question.key,
                question_type=first_question.type,
                question_options=first_question.options,
            )
        except HTTPException:
            llm_question_text = first_question.text
        next_question = IntakeSessionFirstQuestion(
            key=first_question.key,
            text=llm_question_text,
            type=first_question.type,
            options=first_question.options,
        )
        return CreateIntakeSessionResponseLlm(
            mode="llm",
            session_id=created_session.id,
            status=created_session.status,
            current_index=0,
            total_questions=total_questions,
            message=LLM_INTAKE_OPENING_MESSAGE,
            next_question=next_question,
        )

    return CreateIntakeSessionResponseGuided(
        mode="guided",
        session_id=created_session.id,
        status=created_session.status,
        current_index=0,
        total_questions=total_questions,
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
    "/intake-sessions/{session_id}/answers/guided",
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
    current_index = _current_index_for_answered_count(questions, merged_criteria)

    row = await update_intake_session_after_answers(
        client,
        session_id,
        merged_criteria,
    )
    return UpdateIntakeSessionAnswersResponse(
        session=parse_intake_session(row),
        current_index=current_index,
        total_questions=len(questions),
        next_question=next_question,
    )


@router.post(
    "/intake-sessions/{session_id}/answers/llm",
    response_model=SubmitLlmIntakeInputResponse,
)
async def submit_llm_intake_input(
    session_id: UUID,
    body: SubmitLlmIntakeInputRequest,
    client: SupabaseSdkDep,
) -> SubmitLlmIntakeInputResponse:
    session_row = await load_intake_session_row(client, session_id)
    questions = await load_intake_questions(client)
    question_keys = [
        q["key"]
        for q in questions
        if isinstance(q.get("key"), str) and q["key"].strip()
    ]

    current_criteria = session_row.get("criteria")
    existing_criteria = dict(current_criteria) if isinstance(current_criteria, dict) else {}

    parsed = await parse_intake_with_huggingface(
        user_input=body.input,
        existing_criteria=existing_criteria,
        question_keys=question_keys,
        required_fields=list(_REQUIRED_LLM_FIELDS),
    )

    extracted = LlmExtractedIntakePayload.model_validate(parsed["extracted"])
    merged_criteria = parsed["merged_criteria"]
    missing_fields = parsed["missing_fields"]

    next_question = next_question_from_llm_response(
        questions,
        parsed["next_question"],
        missing_fields,
    )

    current_index = _current_index_for_answered_count(questions, merged_criteria)

    await update_intake_session_after_answers(client, session_id, merged_criteria)
    return SubmitLlmIntakeInputResponse(
        extracted=extracted,
        criteria=merged_criteria,
        current_index=current_index,
        total_questions=len(questions),
        missing_fields=missing_fields,
        next_question=next_question,
        is_complete=bool(parsed["is_complete"]),
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
