"""``public.intake_sessions`` (Supabase)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.core.deps import SupabaseSdkDep
from app.domain.intake_criteria import normalize_merged_criteria
from app.domain.intake_validation import compute_current_index
from app.llm import (
    parse_user_input,
    resolve_next_intake_question,
)
from app.llm.intake.service import SKIPPED_FIELDS_KEY
from app.repositories.intake_sessions import (
    get_intake_session_row,
    save_intake_criteria,
)
from app.repositories.questions import list_intake_questions
from app.schemas.intake_sessions import (
    SubmitLlmIntakeInputRequest,
    SubmitLlmIntakeInputResponse,
)

router = APIRouter()


@router.post(
    "/llm",
    response_model=SubmitLlmIntakeInputResponse,
)
async def submit_llm_intake_input(
    session_id: UUID,
    body: SubmitLlmIntakeInputRequest,
    client: SupabaseSdkDep,
) -> SubmitLlmIntakeInputResponse:
    session_row = await get_intake_session_row(client, session_id)
    questions = await list_intake_questions(client)

    current_criteria = session_row.get("criteria")
    current_criteria_dict = dict(current_criteria) if isinstance(current_criteria, dict) else {}

    llm_result = await parse_user_input(
        user_input=body.input,
        current_criteria=current_criteria_dict,
        questions=questions,
    )

    extracted = llm_result["extracted"]
    merged_criteria = normalize_merged_criteria(
        llm_result["merged_criteria"],
        questions,
        reserved_keys=frozenset({SKIPPED_FIELDS_KEY}),
    )
    missing_fields = llm_result["missing_fields"]
    skipped_fields = llm_result["skipped_fields"]
    is_complete = bool(llm_result["is_complete"])

    next_question = resolve_next_intake_question(
        questions,
        llm_result["next_question"],
        missing_fields,
    )

    current_index = compute_current_index(questions, merged_criteria)

    await save_intake_criteria(client, session_id, merged_criteria)

    public_criteria = {k: v for k, v in merged_criteria.items() if k != SKIPPED_FIELDS_KEY}
    question_titles = {
        row["key"]: (row.get("title") or row["key"].replace("_", " ").title())
        for row in questions
        if isinstance(row.get("key"), str)
    }

    return SubmitLlmIntakeInputResponse(
        extracted=extracted,
        criteria=public_criteria,
        current_index=current_index,
        total_questions=len(questions),
        missing_fields=missing_fields,
        skipped_fields=skipped_fields,
        question_titles=question_titles,
        next_question=next_question,
        is_complete=is_complete,
    )
