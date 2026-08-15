"""Run one LLM intake turn.

Extracted from the endpoint so the same pipeline can run in two places: inline behind the
HTTP request today, and inside `chat-intake-worker` once turns are queued (§14.1). Two
copies of this logic would drift, and the drift would be silent — a turn processed by the
worker would merge criteria differently from one processed inline, and nothing would fail.

Nothing here touches FastAPI's request machinery. Failures still surface as
``HTTPException`` because the repositories and providers raise it, and that is
deliberate: the worker classifies a job as retryable or terminal by the status code that
came out (503/504 transient, everything else terminal), so the raisers are the shared
vocabulary rather than an HTTP detail leaking into the queue path.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import HTTPException

from app.clients.bedrock_guardrail import bedrock_guardrail
from app.core.config import settings
from app.domain.intake_criteria import normalize_merged_criteria
from app.domain.intake_validation import compute_current_index
from app.llm import parse_user_input, resolve_next_intake_question
from app.llm.intake.service import SKIPPED_FIELDS_KEY
from app.repositories.intake_sessions import get_intake_session_row, save_intake_criteria
from app.repositories.questions import list_intake_questions
from app.schemas.intake_sessions import (
    IntakeSessionFirstQuestion,
    SubmitLlmIntakeInputResponse,
)
from supabase import AsyncClient

logger = logging.getLogger(__name__)


async def screen_generated_question(
    next_question: IntakeSessionFirstQuestion | None,
) -> IntakeSessionFirstQuestion | None:
    """Screen the model-authored question before it is shown back to the user.

    Off by default (``BEDROCK_GUARDRAIL_SCREEN_OUTPUT``): it doubles the per-turn
    guardrail cost, and this text is template-driven rather than free-form, so it carries
    much less than the user's own message. A blocked question falls back to no text,
    which the client already handles by showing the question row's configured wording.

    Screening the *input* fails closed, because that text is the user's own and is about
    to be stored. The same policy here would be disproportionate: the parse has already
    succeeded, so letting a guardrail outage propagate would requeue the turn on the
    worker — re-paying for the model call — or discard the user's message inline, to
    protect one line of template-driven prose. It degrades to no text instead, which
    costs nothing but the model's phrasing.
    """
    if not settings.bedrock_guardrail_screen_output or next_question is None:
        return next_question
    text = (next_question.text or "").strip()
    if not text:
        return next_question

    try:
        screened = await bedrock_guardrail.screen(text, source="OUTPUT")
    except HTTPException:
        logger.warning("intake_question_screening_unavailable")
        # Screening was asked for and could not run, so the unscreened text is not shown.
        return next_question.model_copy(update={"text": ""})
    if screened.blocked:
        return next_question.model_copy(update={"text": ""})
    return next_question.model_copy(update={"text": screened.text})


def question_titles_for(questions: list[dict[str, Any]]) -> dict[str, str]:
    """Display titles keyed by question key, falling back to a humanised key."""
    return {
        row["key"]: (row.get("title") or row["key"].replace("_", " ").title())
        for row in questions
        if isinstance(row.get("key"), str)
    }


async def run_llm_intake_turn(
    client: AsyncClient,
    *,
    session_id: UUID,
    user_input: str,
) -> SubmitLlmIntakeInputResponse:
    """Parse one user message, merge it into the session, and return the next step."""
    session_row = await get_intake_session_row(client, session_id)
    questions = await list_intake_questions(client)

    current_criteria = session_row.get("criteria")
    current_criteria_dict = dict(current_criteria) if isinstance(current_criteria, dict) else {}

    llm_result = await parse_user_input(
        user_input=user_input,
        current_criteria=current_criteria_dict,
        questions=questions,
    )

    merged_criteria = normalize_merged_criteria(
        llm_result["merged_criteria"],
        questions,
        reserved_keys=frozenset({SKIPPED_FIELDS_KEY}),
    )
    missing_fields = llm_result["missing_fields"]
    is_complete = bool(llm_result["is_complete"])

    next_question = await screen_generated_question(
        resolve_next_intake_question(
            questions,
            llm_result["next_question"],
            missing_fields,
        )
    )
    current_index = compute_current_index(questions, merged_criteria)

    await save_intake_criteria(client, session_id, merged_criteria)

    # The skipped-fields bookkeeping is persisted but never shown: it is how the model is
    # told not to ask again, not a criterion the user chose.
    public_criteria = {k: v for k, v in merged_criteria.items() if k != SKIPPED_FIELDS_KEY}

    return SubmitLlmIntakeInputResponse(
        extracted=llm_result["extracted"],
        criteria=public_criteria,
        current_index=current_index,
        total_questions=len(questions),
        missing_fields=missing_fields,
        skipped_fields=llm_result["skipped_fields"],
        question_titles=question_titles_for(questions),
        next_question=next_question,
        is_complete=is_complete,
    )
