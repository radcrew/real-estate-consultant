"""Result delivery for queued intake turns: SSE stream, with polling as the fallback.

The stream is the primary channel and polling is the retreat, not the reverse — a dropped
``EventSource`` with nothing behind it strands a turn that has already been paid for.
"""

from __future__ import annotations

import time
from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID

import anyio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.core.deps import SupabaseSdkDep
from app.repositories.intake_jobs import get_intake_job_row
from app.schemas.intake_sessions import IntakeJobStatusResponse
from supabase import AsyncClient

router = APIRouter()

TERMINAL_STATUSES = frozenset({"succeeded", "failed"})

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    # Proxies that buffer will hold frames until the response ends, which turns a live
    # stream into one delivery at the very end.
    "X-Accel-Buffering": "no",
}


def job_status_payload(row: dict[str, Any]) -> IntakeJobStatusResponse:
    return IntakeJobStatusResponse(
        job_id=UUID(str(row["id"])),
        status=str(row.get("status") or "queued"),
        result=row.get("result") or None,
        error=row.get("error") or None,
    )


def sse_frame(payload: IntakeJobStatusResponse, *, event: str | None = None) -> str:
    prefix = f"event: {event}\n" if event else ""
    return f"{prefix}data: {payload.model_dump_json()}\n\n"


async def job_event_stream(
    client: AsyncClient,
    *,
    session_id: UUID,
    job_id: UUID,
    timeout_seconds: float,
    poll_interval: float,
) -> AsyncIterator[str]:
    """Emit the job's state until it settles, the deadline passes, or the client leaves.

    Polling Postgres rather than listening for notifications keeps this to one moving
    part: the worker writes the row it would have to write anyway, and a client that
    reconnects mid-turn sees current state on its first frame instead of waiting for the
    next change.
    """
    deadline = time.monotonic() + timeout_seconds
    while True:
        row = await get_intake_job_row(client, session_id=session_id, job_id=job_id)
        payload = job_status_payload(row)
        yield sse_frame(payload)

        if payload.status in TERMINAL_STATUSES:
            return
        if time.monotonic() >= deadline:
            # Named so the client can tell "still running, stop watching" apart from
            # "finished": the job may yet complete, and polling can pick it up.
            yield sse_frame(payload, event="timeout")
            return
        await anyio.sleep(poll_interval)


@router.get("/{job_id}", response_model=IntakeJobStatusResponse)
async def get_intake_job(
    session_id: UUID,
    job_id: UUID,
    client: SupabaseSdkDep,
) -> IntakeJobStatusResponse:
    """Poll one job. The fallback when an SSE connection drops."""
    row = await get_intake_job_row(client, session_id=session_id, job_id=job_id)
    return job_status_payload(row)


@router.get("/{job_id}/stream")
async def stream_intake_job(
    session_id: UUID,
    job_id: UUID,
    client: SupabaseSdkDep,
) -> StreamingResponse:
    """Follow one job until it settles."""
    # Read once up front so an unknown or foreign job answers 404 properly. Raising from
    # inside the generator would be too late: the response has already begun, and the
    # client would receive a 200 that simply stops.
    await get_intake_job_row(client, session_id=session_id, job_id=job_id)
    return StreamingResponse(
        job_event_stream(
            client,
            session_id=session_id,
            job_id=job_id,
            timeout_seconds=settings.chat_job_timeout_seconds,
            poll_interval=settings.chat_job_poll_interval_seconds,
        ),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )
