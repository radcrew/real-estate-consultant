"""``POST /intake-sessions/{session_id}/answers/llm`` — enqueue one intake turn."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
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
from app.repositories.intake_sessions import get_owned_intake_session_row
from app.schemas.intake_sessions import (
    EnqueuedLlmIntakeJobResponse,
    SubmitLlmIntakeInputRequest,
)
from app.services.intake_jobs import execute_claimed_job
from app.utils.exceptions import raise_too_many_requests

router = APIRouter()


@router.post(
    "/llm",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=EnqueuedLlmIntakeJobResponse,
    # Anonymous and metered per request: without this, one caller can spend the provider
    # budget unattended — and behind a queue, keep spending from the backlog.
    dependencies=[AdmitIntakeLlmTurn],
)
async def submit_llm_intake_input(
    session_id: UUID,
    body: SubmitLlmIntakeInputRequest,
    client: SupabaseSdkDep,
    current_user: CurrentUser,
) -> EnqueuedLlmIntakeJobResponse:
    """Accept a turn and return the job to follow.

    The result arrives over ``GET .../jobs/{job_id}/stream``, with the poll endpoint as
    the fallback. Returning ``202`` rather than the turn itself is what makes a provider
    stall survivable: the user's text is already durable before any model is called.
    """
    # Also the ownership check: a session belonging to someone else answers 404 exactly
    # like a missing one, so a guessed id learns nothing. Doing it here keeps every later
    # step — the sweep, the job row, the queue — working on a session the caller owns.
    await get_owned_intake_session_row(client, session_id, user_id=UUID(current_user.id))

    # Swept here because this is where a dead row does its damage: an unfinished job
    # holds the session's in-flight slot, so one that nothing will ever complete locks
    # the user out of their own conversation permanently. Both unfinished states can get
    # stuck, for different reasons and on different timescales — `running` when a worker
    # is killed mid-turn (the claim gate stops redelivery from rescuing it), `queued`
    # when nothing ever picks the job up.
    #
    # Only this session's rows: that is the slot being freed, and it keeps a per-request
    # sweep off every other conversation's rows. Other sessions' dead rows are cleared
    # when they next send a turn, or by a scheduled sweep — they harm nobody meanwhile.
    now = datetime.now(UTC)
    await expire_stale_running_jobs(
        client,
        session_id=session_id,
        older_than=now - timedelta(seconds=settings.chat_job_stale_after_seconds),
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
