"""``public.intake_sessions`` (Supabase)."""

from __future__ import annotations

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
from app.models.intake_sessions import IntakeSession
from app.repositories.intake_sessions import (
    create_intake_session_row,
    load_intake_session_row,
    parse_intake_session,
)
from app.repositories.questions import (
    load_intake_questions,
    map_question_to_model,
)
from app.repositories.search_profiles import ensure_search_profile_access
from app.schemas.intake_sessions import (
    CreateIntakeSessionGuidedResponse,
    CreateIntakeSessionLlmResponse,
    CreateIntakeSessionResponse,
    IntakeSessionFirstQuestion,
)

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
    questions = await load_intake_questions(client)
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
        except HTTPException:
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
    response_model=IntakeSession,
)
async def get_intake_session(
    session_id: UUID,
    client: SupabaseSdkDep,
    current_user: CurrentUser,
) -> IntakeSession:
    session_row = await load_intake_session_row(client, session_id)
    await ensure_search_profile_access(
        client,
        session_row.get("search_profile_id"),
        current_user.id,
    )
    return parse_intake_session(session_row)
