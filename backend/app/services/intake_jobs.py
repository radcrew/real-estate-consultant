"""Run a claimed intake job and record its outcome.

Shared by the queued worker and the inline path the endpoint takes when no queue is
configured. Both must leave the same row behind — a turn that succeeded inline and one
that succeeded on the worker are the same turn, and a client reading the job cannot tell
which ran it.
"""

from __future__ import annotations

import logging
from typing import NamedTuple
from uuid import UUID

from fastapi import HTTPException

from app.repositories.intake_jobs import complete_intake_job, fail_intake_job
from app.services.intake_llm import run_llm_intake_turn
from supabase import AsyncClient

# The §8 raisers meaning "the provider was unreachable", as opposed to "it answered and
# the answer was unusable". Only these are worth another delivery.
RETRYABLE_STATUS = frozenset({503, 504})

logger = logging.getLogger(__name__)


class JobOutcome(NamedTuple):
    status: str
    retryable: bool


async def execute_claimed_job(
    client: AsyncClient,
    *,
    job_id: UUID,
    session_id: UUID,
    user_input: str,
    allow_retry: bool,
) -> JobOutcome:
    """Run one already-claimed job to a recorded conclusion.

    ``allow_retry`` must be false wherever nothing will redeliver the message. Leaving a
    row ``queued`` with no queue behind it strands the turn forever: the client polls a
    job that no one will ever pick up, and the stale-claim sweeper does not cover
    ``queued`` rows because it cannot tell them from ones legitimately waiting.
    """
    try:
        response = await run_llm_intake_turn(
            client,
            session_id=session_id,
            user_input=user_input,
        )
    except HTTPException as exc:
        retryable = allow_retry and exc.status_code in RETRYABLE_STATUS
        await fail_intake_job(
            client,
            job_id=job_id,
            error=str(exc.detail),
            retryable=retryable,
        )
        logger.warning(
            "intake_job_failed",
            extra={
                "job_id": str(job_id),
                "status_code": exc.status_code,
                "retryable": retryable,
            },
        )
        return JobOutcome(status="queued" if retryable else "failed", retryable=retryable)

    await complete_intake_job(
        client,
        job_id=job_id,
        # mode="json" so nested models and any UUID/datetime land as jsonb-safe values.
        result_payload=response.model_dump(mode="json"),
    )
    logger.info("intake_job_succeeded", extra={"job_id": str(job_id)})
    return JobOutcome(status="succeeded", retryable=False)
