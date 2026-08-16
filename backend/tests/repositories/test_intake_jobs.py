"""Tests for ``public.intake_jobs`` persistence."""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.repositories.intake_jobs import (
    claim_intake_job,
    complete_intake_job,
    count_active_intake_jobs,
    create_intake_job,
    expire_abandoned_queued_jobs,
    expire_stale_running_jobs,
    fail_intake_job,
    get_intake_job_row,
)
from tests.repositories.conftest import make_supabase_client

_SESSION_ID = uuid4()
_JOB_ID = uuid4()

_JOB_ROW = {
    "id": str(_JOB_ID),
    "session_id": str(_SESSION_ID),
    "status": "queued",
    "input": "warehouse in Austin",
    "result": None,
    "error": None,
    "attempts": 0,
}


class TestCreateIntakeJob:
    async def test_returns_the_inserted_row(self):
        client = make_supabase_client([_JOB_ROW])
        row = await create_intake_job(
            client, session_id=_SESSION_ID, user_input="warehouse in Austin"
        )
        assert row == _JOB_ROW

    async def test_inserts_queued_with_the_users_text(self):
        """The input is stored so a redrive can replay the turn instead of losing it."""
        client = make_supabase_client([_JOB_ROW])
        await create_intake_job(client, session_id=_SESSION_ID, user_input="warehouse in Austin")
        client.table.return_value.insert.assert_called_once_with(
            {
                "session_id": str(_SESSION_ID),
                "input": "warehouse in Austin",
                "status": "queued",
            },
        )


class TestGetIntakeJobRow:
    async def test_returns_the_row(self):
        client = make_supabase_client([_JOB_ROW])
        assert await get_intake_job_row(
            client, session_id=_SESSION_ID, job_id=_JOB_ID
        ) == _JOB_ROW

    async def test_scopes_the_read_to_the_session(self):
        """A job id alone must not read another session's turn."""
        client = make_supabase_client([_JOB_ROW])
        await get_intake_job_row(client, session_id=_SESSION_ID, job_id=_JOB_ID)
        filters = {c.args for c in client.table.return_value.eq.call_args_list}
        assert ("id", str(_JOB_ID)) in filters
        assert ("session_id", str(_SESSION_ID)) in filters

    async def test_missing_job_raises_404(self):
        client = make_supabase_client([])
        with pytest.raises(HTTPException) as info:
            await get_intake_job_row(client, session_id=_SESSION_ID, job_id=_JOB_ID)
        assert info.value.status_code == 404

    async def test_foreign_job_is_indistinguishable_from_a_missing_one(self):
        """A job id is a bearer token; "exists but not yours" is itself a disclosure."""
        client = make_supabase_client([])
        with pytest.raises(HTTPException) as info:
            await get_intake_job_row(client, session_id=uuid4(), job_id=_JOB_ID)
        assert info.value.detail == "Intake job not found."


class TestCountActiveIntakeJobs:
    async def test_counts_unfinished_turns(self):
        client = make_supabase_client([{"id": "a"}, {"id": "b"}])
        assert await count_active_intake_jobs(client, session_id=_SESSION_ID) == 2

    async def test_only_queued_and_running_count(self):
        client = make_supabase_client([])
        await count_active_intake_jobs(client, session_id=_SESSION_ID)
        client.table.return_value.in_.assert_called_once_with("status", ["queued", "running"])


class TestClaimIntakeJob:
    async def test_claim_returns_the_row(self):
        client = make_supabase_client([{**_JOB_ROW, "status": "running"}])
        claimed = await claim_intake_job(client, job_id=_JOB_ID)
        assert claimed is not None
        assert claimed["status"] == "running"

    async def test_second_delivery_of_a_claimed_job_is_a_no_op(self):
        """The idempotency gate: without it, redelivery pays for the turn twice."""
        client = make_supabase_client([])
        assert await claim_intake_job(client, job_id=_JOB_ID) is None

    async def test_claim_is_conditional_on_still_being_queued(self):
        client = make_supabase_client([_JOB_ROW])
        await claim_intake_job(client, job_id=_JOB_ID)
        table = client.table.return_value
        filters = {c.args for c in table.eq.call_args_list}
        assert ("status", "queued") in filters
        table.update.assert_called_once_with({"status": "running"})

    async def test_attempts_is_left_to_the_trigger(self):
        """PostgREST cannot express attempts = attempts + 1, and a read-then-write races."""
        client = make_supabase_client([_JOB_ROW])
        await claim_intake_job(client, job_id=_JOB_ID)
        payload = client.table.return_value.update.call_args.args[0]
        assert "attempts" not in payload


class TestCompleteIntakeJob:
    async def test_stores_the_result(self):
        client = make_supabase_client([{**_JOB_ROW, "status": "succeeded"}])
        payload = {"extracted": {"location": "Austin"}}
        row = await complete_intake_job(client, job_id=_JOB_ID, result_payload=payload)
        assert row is not None
        client.table.return_value.update.assert_called_once_with(
            {"status": "succeeded", "result": payload, "error": None},
        )

    async def test_only_a_running_job_can_succeed(self):
        client = make_supabase_client([])
        assert await complete_intake_job(client, job_id=_JOB_ID, result_payload={}) is None


class TestFailIntakeJob:
    async def test_transient_failure_goes_back_to_queued(self):
        """Redelivery is the retry budget for throttling and timeouts."""
        client = make_supabase_client([{**_JOB_ROW, "status": "queued"}])
        await fail_intake_job(client, job_id=_JOB_ID, error="throttled", retryable=True)
        client.table.return_value.update.assert_called_once_with(
            {"status": "queued", "error": "throttled"},
        )

    async def test_terminal_failure_stops(self):
        """A parse failure redelivered burns quota re-earning the same error."""
        client = make_supabase_client([{**_JOB_ROW, "status": "failed"}])
        await fail_intake_job(client, job_id=_JOB_ID, error="bad reply", retryable=False)
        client.table.return_value.update.assert_called_once_with(
            {"status": "failed", "error": "bad reply"},
        )


class TestExpireStaleRunningJobs:
    async def test_fails_jobs_whose_worker_never_reported(self):
        """A worker killed mid-turn leaves a claim redelivery can no longer rescue."""
        cutoff = datetime(2026, 8, 14, 12, 0, tzinfo=UTC)
        client = make_supabase_client([_JOB_ROW])
        rows = await expire_stale_running_jobs(
            client, session_id=_SESSION_ID, older_than=cutoff
        )
        assert rows == [_JOB_ROW]
        table = client.table.return_value
        table.eq.assert_any_call("status", "running")
        table.lt.assert_called_once_with("updated_at", cutoff.isoformat())

    async def test_only_touches_the_given_session(self):
        # Unscoped, this ran table-wide on every enqueue: no index covers it, and
        # concurrent turns in unrelated conversations contend for the same rows.
        client = make_supabase_client([_JOB_ROW])
        await expire_stale_running_jobs(
            client,
            session_id=_SESSION_ID,
            older_than=datetime(2026, 8, 14, 12, 0, tzinfo=UTC),
        )
        client.table.return_value.eq.assert_any_call("session_id", str(_SESSION_ID))


class TestExpireAbandonedQueuedJobs:
    async def test_fails_jobs_nothing_ever_picked_up(self):
        """A queued row counts against the in-flight cap, so one that is never claimed
        locks the session permanently — reachable by a failed publish, a worker that is
        down, or a message that exhausted maxReceiveCount into the DLQ."""
        cutoff = datetime(2026, 8, 14, 12, 0, tzinfo=UTC)
        client = make_supabase_client([_JOB_ROW])
        rows = await expire_abandoned_queued_jobs(
            client, session_id=_SESSION_ID, older_than=cutoff
        )
        assert rows == [_JOB_ROW]
        table = client.table.return_value
        table.eq.assert_any_call("status", "queued")
        table.lt.assert_called_once_with("updated_at", cutoff.isoformat())

    async def test_only_touches_the_given_session(self):
        client = make_supabase_client([_JOB_ROW])
        await expire_abandoned_queued_jobs(
            client,
            session_id=_SESSION_ID,
            older_than=datetime(2026, 8, 14, 12, 0, tzinfo=UTC),
        )
        client.table.return_value.eq.assert_any_call("session_id", str(_SESSION_ID))

    async def test_it_is_terminal_not_a_requeue(self):
        """Requeuing would recreate the state it exists to clear."""
        client = make_supabase_client([_JOB_ROW])
        await expire_abandoned_queued_jobs(
            client, session_id=_SESSION_ID, older_than=datetime(2026, 8, 14, 12, 0, tzinfo=UTC)
        )
        payload = client.table.return_value.update.call_args.args[0]
        assert payload["status"] == "failed"
