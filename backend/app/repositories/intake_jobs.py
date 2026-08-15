"""Persistence for ``public.intake_jobs`` (Supabase PostgREST).

One row per queued intake turn. The row is both the result store the client reads and the
ledger that makes SQS redelivery safe — see the migration for why those are the same
table.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID

from app.core.db_safe import execute_db_safe
from app.repositories.exceptions import raise_intake_job_not_found
from app.utils.supabase.response import as_row_list, get_single_row
from supabase import AsyncClient

IntakeJobStatus = Literal["queued", "running", "succeeded", "failed"]

ACTIVE_STATUSES: tuple[str, ...] = ("queued", "running")

_SELECT = (
    "id, session_id, status, input, result, error, attempts, "
    "created_at, updated_at, started_at, finished_at"
)


async def create_intake_job(
    client: AsyncClient,
    *,
    session_id: UUID,
    user_input: str,
) -> dict[str, Any]:
    """Insert a ``queued`` job. Called before the SQS publish, never after."""
    result = await execute_db_safe(
        client.table("intake_jobs")
        .insert({"session_id": str(session_id), "input": user_input, "status": "queued"})
        .execute(),
    )
    return get_single_row(result, detail="Unexpected response creating intake job.")


async def get_intake_job_row(
    client: AsyncClient,
    *,
    session_id: UUID,
    job_id: UUID,
) -> dict[str, Any]:
    """Load one job, scoped to its session.

    The session filter is the access control: a job id on its own must not be able to
    read another session's turn.
    """
    result = await execute_db_safe(
        client.table("intake_jobs")
        .select(_SELECT)
        .eq("id", str(job_id))
        .eq("session_id", str(session_id))
        .limit(1)
        .execute(),
    )
    if not as_row_list(result.data):
        raise_intake_job_not_found()
    return get_single_row(result, detail="Unexpected response loading intake job.")


async def count_active_intake_jobs(client: AsyncClient, *, session_id: UUID) -> int:
    """How many turns for this session are unfinished."""
    result = await execute_db_safe(
        client.table("intake_jobs")
        .select("id")
        .eq("session_id", str(session_id))
        .in_("status", list(ACTIVE_STATUSES))
        .execute(),
    )
    return len(as_row_list(result.data))


async def claim_intake_job(client: AsyncClient, *, job_id: UUID) -> dict[str, Any] | None:
    """Move ``queued`` -> ``running``, or return ``None`` if someone already did.

    This conditional update is the idempotency gate, and the only thing standing between
    SQS at-least-once delivery and paying twice for one turn: a redelivered message whose
    job already ran matches no row, so the worker drops it instead of re-invoking the
    provider. ``attempts`` is incremented by trigger, not here.
    """
    result = await execute_db_safe(
        client.table("intake_jobs")
        .update({"status": "running"})
        .eq("id", str(job_id))
        .eq("status", "queued")
        .execute(),
    )
    rows = as_row_list(result.data)
    return rows[0] if rows else None


async def complete_intake_job(
    client: AsyncClient,
    *,
    job_id: UUID,
    result_payload: dict[str, Any],
) -> dict[str, Any] | None:
    """Store the turn's result and mark the job succeeded."""
    result = await execute_db_safe(
        client.table("intake_jobs")
        .update({"status": "succeeded", "result": result_payload, "error": None})
        .eq("id", str(job_id))
        .eq("status", "running")
        .execute(),
    )
    rows = as_row_list(result.data)
    return rows[0] if rows else None


async def fail_intake_job(
    client: AsyncClient,
    *,
    job_id: UUID,
    error: str,
    retryable: bool,
) -> dict[str, Any] | None:
    """Record a failed turn.

    ``retryable`` decides whether the job goes back to ``queued`` for redelivery or stops
    at ``failed``. Getting that backwards is expensive in both directions: a transient
    fault marked terminal loses a turn the user could have had, and a deterministic one
    marked transient burns quota re-earning the same error until the DLQ catches it.
    """
    status: IntakeJobStatus = "queued" if retryable else "failed"
    updated = await execute_db_safe(
        client.table("intake_jobs")
        .update({"status": status, "error": error})
        .eq("id", str(job_id))
        .eq("status", "running")
        .execute(),
    )
    rows = as_row_list(updated.data)
    return rows[0] if rows else None


async def expire_stale_running_jobs(
    client: AsyncClient,
    *,
    older_than: datetime,
) -> list[dict[str, Any]]:
    """Fail jobs stuck in ``running`` since before ``older_than``.

    A worker killed mid-turn — Lambda timeout, OOM — leaves a claimed row nobody will
    ever finish, and the claim gate means redelivery cannot rescue it. Without this the
    client waits out its whole timeout on a job that is already dead.
    """
    result = await execute_db_safe(
        client.table("intake_jobs")
        .update({"status": "failed", "error": "Worker did not report a result."})
        .eq("status", "running")
        .lt("updated_at", older_than.astimezone(UTC).isoformat())
        .execute(),
    )
    return as_row_list(result.data)


async def expire_abandoned_queued_jobs(
    client: AsyncClient,
    *,
    older_than: datetime,
) -> list[dict[str, Any]]:
    """Fail jobs still ``queued`` since before ``older_than`` — nothing will run them.

    A queued row counts against the session's in-flight cap, so one that is never picked
    up locks the user out of their own conversation permanently. Three ways to get there,
    one of them by design: a failed SQS publish deliberately leaves the row behind, a
    worker that is down never claims it, and a message that exhausts ``maxReceiveCount``
    goes to the DLQ while its row stays put.

    ``older_than`` must be well past ``visibilityTimeout x maxReceiveCount``. A job being
    legitimately retried sits in ``queued`` between deliveries, and expiring it there
    would cancel work SQS is still going to hand over. ``updated_at`` moves on every
    status change, so a job that is actively cycling keeps looking fresh — only one that
    nothing has touched at all ages out.
    """
    result = await execute_db_safe(
        client.table("intake_jobs")
        .update({"status": "failed", "error": "This message was never picked up."})
        .eq("status", "queued")
        .lt("updated_at", older_than.astimezone(UTC).isoformat())
        .execute(),
    )
    return as_row_list(result.data)
