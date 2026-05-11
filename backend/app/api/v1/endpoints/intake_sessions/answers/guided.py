"""``public.intake_sessions`` (Supabase)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.core.deps import SupabaseSdkDep
from app.exceptions.intake import raise_intake_unknown_question_key
from app.repositories.intake_sessions import (
    append_intake_criteria_answer,
    load_intake_session_row,
    parse_intake_session,
    save_intake_criteria,
)
from app.repositories.questions import (
    load_intake_questions,
    map_question_to_model,
    next_question_row_after_order,
    order_for_question_key,
)
from app.schemas.intake_sessions import (
    UpdateIntakeSessionAnswersRequest,
    UpdateIntakeSessionAnswersResponse,
)
from app.utils.intake_validation import compute_current_index

router = APIRouter()

@router.patch(
    "/guided",
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
        raise_intake_unknown_question_key()

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
