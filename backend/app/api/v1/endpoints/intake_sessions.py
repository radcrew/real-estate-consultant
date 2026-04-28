"""``public.intake_sessions`` (Supabase)."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import CurrentUser, SupabaseSdkDep
from app.llm import (
    INTAKE_OPENING_MESSAGE,
    extract_intake_with_huggingface,
    generate_opening_question_with_huggingface,
    resolve_next_intake_question,
)
from app.models.intake_sessions import IntakeSession
from app.repositories.intake_sessions import (
    append_intake_criteria_answer,
    create_intake_session_row,
    load_intake_session_row,
    parse_intake_session,
    save_intake_criteria,
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
    IntakeSessionFirstQuestion,
    LlmExtractedIntakePayload,
    SubmitLlmIntakeInputRequest,
    SubmitLlmIntakeInputResponse,
    UpdateIntakeSessionAnswersRequest,
    UpdateIntakeSessionAnswersResponse,
)

router = APIRouter(tags=["intake-sessions"])


def _has_answer(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) > 0
    return True


def compute_current_index(questions: list[dict], criteria: object) -> int:
    if not questions or not isinstance(criteria, dict):
        return 0
    count = 0
    for row in questions:
        question_key = row.get("key")
        if not isinstance(question_key, str):
            continue
        if _has_answer(criteria.get(question_key)):
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
    """Create an intake session (guided: first question; LLM: welcome + next prompt)."""
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
            llm_question_text = await generate_opening_question_with_huggingface(
                welcome_message=INTAKE_OPENING_MESSAGE,
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
            message=INTAKE_OPENING_MESSAGE,
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
    current_index = compute_current_index(questions, merged_criteria)

    row = await save_intake_criteria(client, session_id, merged_criteria)
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

    current_criteria = session_row.get("criteria")
    validated_criteria = dict(current_criteria) if isinstance(current_criteria, dict) else {}

    llm_result = await extract_intake_with_huggingface(
        user_input=body.input,
        validated_criteria=validated_criteria,
        questions=questions,
    )

    extracted = LlmExtractedIntakePayload.model_validate(llm_result["extracted"])
    merged_criteria = llm_result["merged_criteria"]
    missing_fields = llm_result["missing_fields"]
    is_complete = bool(llm_result["is_complete"])

    next_question = resolve_next_intake_question(
        questions,
        llm_result["next_question"],
        missing_fields,
    )

    current_index = compute_current_index(questions, merged_criteria)

    await save_intake_criteria(client, session_id, merged_criteria)
    return SubmitLlmIntakeInputResponse(
        extracted=extracted,
        criteria=merged_criteria,
        current_index=current_index,
        total_questions=len(questions),
        missing_fields=missing_fields,
        next_question=next_question,
        is_complete=is_complete,
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
