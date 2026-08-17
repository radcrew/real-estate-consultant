"""Result delivery for queued intake turns: the client polls this.

An SSE stream was built here first and removed. These routes sit on the protected router,
so they require a bearer token, and ``EventSource`` cannot set headers — every browser
connection 401'd and silently fell through to polling. The tests did not catch it because
they override ``get_current_user``, so the auth requirement was never exercised.

Two ways back to streaming, if the latency ever justifies one: read the token with
``fetch`` + ``ReadableStream`` instead of ``EventSource``, or move to a transport that
carries credentials. Do not simply re-add ``EventSource`` — it cannot authenticate here.
Polling also avoids holding a serverless function per waiting client, which §21 of the
architecture doc already listed as the cheaper option.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter

from app.core.deps import CurrentUser, SupabaseSdkDep
from app.repositories.intake_jobs import get_intake_job_row
from app.repositories.intake_sessions import get_owned_intake_session_row
from app.schemas.intake_sessions import IntakeJobStatusResponse

router = APIRouter()

TERMINAL_STATUSES = frozenset({"succeeded", "failed"})


def job_status_payload(row: dict[str, Any]) -> IntakeJobStatusResponse:
    return IntakeJobStatusResponse(
        job_id=UUID(str(row["id"])),
        status=str(row.get("status") or "queued"),
        result=row.get("result") or None,
        error=row.get("error") or None,
    )


@router.get("/{job_id}", response_model=IntakeJobStatusResponse)
async def get_intake_job(
    session_id: UUID,
    job_id: UUID,
    client: SupabaseSdkDep,
    current_user: CurrentUser,
) -> IntakeJobStatusResponse:
    """Return one job's current state.

    Deliberately unmetered: the client asks about once a second while a turn runs, so any
    budget tight enough to matter would break the delivery path itself.

    The session lookup is a second indexed read on a route polled once a second, and it
    is worth it — a job's result carries the criteria extracted from someone's message,
    so scoping by session alone would make two guessed UUIDs enough to read it.
    """
    await get_owned_intake_session_row(client, session_id, user_id=UUID(current_user.id))
    row = await get_intake_job_row(client, session_id=session_id, job_id=job_id)
    return job_status_payload(row)
