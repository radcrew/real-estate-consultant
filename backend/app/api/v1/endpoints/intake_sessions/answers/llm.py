"""``POST /intake-sessions/{session_id}/answers/llm`` — enqueue one intake turn."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from app.clients.sqs import chat_job_queue
from app.core.config import settings
from app.core.deps import SupabaseSdkDep
from app.core.intake_admission import AdmitIntakeLlmTurn
from app.repositories.intake_jobs import (
    claim_intake_job,
    count_active_intake_jobs,
    create_intake_job,
)
from app.repositories.intake_sessions import get_intake_session_row
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
) -> EnqueuedLlmIntakeJobResponse:
    """Accept a turn and return the job to follow.

    The result arrives over ``GET .../jobs/{job_id}/stream``, with the poll endpoint as
    the fallback. Returning ``202`` rather than the turn itself is what makes a provider
    stall survivable: the user's text is already durable before any model is called.
    """
    # A missing session must 404 here rather than surfacing as a foreign-key error from
    # the insert below.
    await get_intake_session_row(client, session_id)

    active = await count_active_intake_jobs(client, session_id=session_id)
    if active >= settings.intake_max_active_jobs_per_session:
        raise_too_many_requests(
            "Still working on your last message. Please wait for it to finish.",
        )

    # Written before the publish: a row with no message is visible and redrivable, while
    # a message with no row is undiagnosable when the consumer picks it up.
    job = await create_intake_job(client, session_id=session_id, user_input=body.input)
    job_id = UUID(str(job["id"]))

    if chat_job_queue.enabled:
        await chat_job_queue.publish(job_id=job_id, session_id=session_id)
        return EnqueuedLlmIntakeJobResponse(job_id=job_id, status="queued")

    # No queue configured — local development and the test suite. The turn runs inline
    # and lands terminal, so the client contract is byte-identical either way.
    claimed = await claim_intake_job(client, job_id=job_id)
    if claimed is None:  # pragma: no cover — nothing else can claim a row created here
        return EnqueuedLlmIntakeJobResponse(job_id=job_id, status="queued")
    outcome = await execute_claimed_job(
        client,
        job_id=job_id,
        session_id=session_id,
        user_input=body.input,
        # Nothing would redeliver it, so a transient fault must still end the job rather
        # than stranding it as queued forever.
        allow_retry=False,
    )
    return EnqueuedLlmIntakeJobResponse(job_id=job_id, status=outcome.status)
