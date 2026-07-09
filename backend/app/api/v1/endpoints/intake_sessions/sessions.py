"""``public.intake_sessions`` (Supabase)."""

from __future__ import annotations

import logging
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.v1.endpoints.intake_sessions.exceptions import (
    raise_intake_endpoint_no_questions_configured,
)
from app.core.deps import CurrentUser, SupabaseSdkDep
from app.llm import (
    INTAKE_OPENING_MESSAGE,
    generate_opening_question,
)
from app.repositories.intake_sessions import (
    create_intake_session_row,
    get_intake_session_row,
    parse_intake_session,
)
from app.repositories.questions import (
    list_intake_questions,
    map_question_to_model,
)
from app.repositories.search_profiles import ensure_search_profile_access
from app.schemas.intake_sessions import (
    CreateIntakeSessionGuidedResponse,
    CreateIntakeSessionLlmResponse,
    CreateIntakeSessionResponse,
    GetIntakeSessionResponse,
    IntakeSessionFirstQuestion,
)
from app.utils.intake_validation import compute_current_index, has_answer

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/",
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
    created_session = await create_intake_session_row(client)
    questions = await list_intake_questions(client)
    total_questions = len(questions)

    if not questions:
        raise_intake_endpoint_no_questions_configured()

    first_question = map_question_to_model(questions[0])

    if mode == "llm":
        try:
            llm_question_text = await generate_opening_question(
                welcome_message=INTAKE_OPENING_MESSAGE,
                key=first_question.key,
                type=first_question.type,
                options=first_question.options,
            )
        except HTTPException as exc:
            logger.warning(
                "llm_opening_question_failed",
                extra={"status_code": exc.status_code, "detail": exc.detail},
            )
            llm_question_text = first_question.text

        next_question = IntakeSessionFirstQuestion(
            key=first_question.key,
            title=first_question.title,
            text=llm_question_text,
            type=first_question.type,
            options=first_question.options,
        )
        return CreateIntakeSessionLlmResponse(
            mode="llm",
            session_id=created_session.id,
            status=created_session.status,
            current_index=0,
            total_questions=total_questions,
            message=INTAKE_OPENING_MESSAGE,
            next_question=next_question,
        )

    return CreateIntakeSessionGuidedResponse(
        mode="guided",
        session_id=created_session.id,
        status=created_session.status,
        current_index=0,
        total_questions=total_questions,
        first_question=first_question,
    )


@router.get(
    "/{session_id}",
    response_model=GetIntakeSessionResponse,
)
async def get_intake_session(
    session_id: UUID,
    client: SupabaseSdkDep,
    current_user: CurrentUser,
) -> GetIntakeSessionResponse:
    session_row = await get_intake_session_row(client, session_id)
    await ensure_search_profile_access(
        client,
        session_row.get("search_profile_id"),
        current_user.id,
    )
    session = parse_intake_session(session_row)
    questions = await list_intake_questions(client)
    criteria = session.criteria if isinstance(session.criteria, dict) else {}

    question_history: list[IntakeSessionFirstQuestion] = []
    next_question: IntakeSessionFirstQuestion | None = None

    for question in questions:
        question_key = question.get("key")
        is_answered = isinstance(question_key, str) and has_answer(criteria.get(question_key))
        if is_answered:
            question_history.append(map_question_to_model(question))
        elif next_question is None:
            next_question = map_question_to_model(question)

    return GetIntakeSessionResponse(
        **session.model_dump(),
        current_index=compute_current_index(questions, criteria),
        total_questions=len(questions),
        question_history=question_history,
        next_question=next_question,
    )
