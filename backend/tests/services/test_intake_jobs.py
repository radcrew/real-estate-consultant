"""Tests for the shared claimed-job runner.

Both the queued worker and the endpoint's inline path go through this, so the row a turn
leaves behind does not depend on which one ran it.
"""
from __future__ import annotations

import asyncio
from contextlib import ExitStack
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.services.intake_jobs import UNEXPECTED_FAILURE, JobOutcome, execute_claimed_job

_SERVICE = "app.services.intake_jobs"
_JOB_ID = uuid4()
_SESSION_ID = uuid4()


def _turn_response():
    response = MagicMock()
    response.model_dump.return_value = {"is_complete": True}
    return response


def _enter(stack, *, turn=None):
    run = turn or AsyncMock(return_value=_turn_response())
    complete = AsyncMock(return_value={})
    fail = AsyncMock(return_value={})
    for item in (
        patch(f"{_SERVICE}.run_llm_intake_turn", run),
        patch(f"{_SERVICE}.complete_intake_job", complete),
        patch(f"{_SERVICE}.fail_intake_job", fail),
    ):
        stack.enter_context(item)
    return run, complete, fail


async def _execute(*, allow_retry: bool, turn=None, stack=None):
    return await execute_claimed_job(
        MagicMock(),
        job_id=_JOB_ID,
        session_id=_SESSION_ID,
        user_input="warehouse in Austin",
        allow_retry=allow_retry,
    )


class TestSuccess:
    async def test_records_the_result(self):
        with ExitStack() as stack:
            _, complete, _ = _enter(stack)
            outcome = await _execute(allow_retry=True)
        assert outcome.status == "succeeded"
        assert outcome.retryable is False
        assert complete.await_args.kwargs["result_payload"] == {"is_complete": True}

    async def test_result_is_serialised_for_jsonb(self):
        response = _turn_response()
        with ExitStack() as stack:
            _enter(stack, turn=AsyncMock(return_value=response))
            await _execute(allow_retry=True)
        response.model_dump.assert_called_once_with(mode="json")


class TestFailureClassification:
    @pytest.mark.parametrize("status", [503, 504])
    async def test_transient_faults_requeue_when_redelivery_exists(self, status):
        failing = AsyncMock(side_effect=HTTPException(status_code=status, detail="busy"))
        with ExitStack() as stack:
            _, _, fail = _enter(stack, turn=failing)
            outcome = await _execute(allow_retry=True)
        assert outcome == ("queued", True)
        assert fail.await_args.kwargs["retryable"] is True

    @pytest.mark.parametrize("status", [400, 404, 422, 502])
    async def test_deterministic_faults_stop(self, status):
        failing = AsyncMock(side_effect=HTTPException(status_code=status, detail="nope"))
        with ExitStack() as stack:
            _, _, fail = _enter(stack, turn=failing)
            outcome = await _execute(allow_retry=True)
        assert outcome == ("failed", False)
        assert fail.await_args.kwargs["retryable"] is False

    @pytest.mark.parametrize("status", [503, 504])
    async def test_without_redelivery_even_transient_faults_are_terminal(self, status):
        """Inline, nothing would pick the job back up: 'queued' would strand it forever,
        with the client polling a turn no one will ever run."""
        failing = AsyncMock(side_effect=HTTPException(status_code=status, detail="busy"))
        with ExitStack() as stack:
            _, _, fail = _enter(stack, turn=failing)
            outcome = await _execute(allow_retry=False)
        assert outcome == ("failed", False)
        assert fail.await_args.kwargs["retryable"] is False

    async def test_the_error_reaches_the_row(self):
        failing = AsyncMock(side_effect=HTTPException(status_code=502, detail="bad reply"))
        with ExitStack() as stack:
            _, _, fail = _enter(stack, turn=failing)
            await _execute(allow_retry=True)
        assert fail.await_args.kwargs["error"] == "bad reply"

    async def test_a_failed_turn_stores_no_result(self):
        failing = AsyncMock(side_effect=HTTPException(status_code=502, detail="bad reply"))
        with ExitStack() as stack:
            _, complete, _ = _enter(stack, turn=failing)
            await _execute(allow_retry=True)
        complete.assert_not_awaited()


class TestUnexpectedFailure:
    """Anything not raised as an HTTPException still has to land on the row."""

    async def test_it_is_recorded_rather_than_escaping(self):
        # Escaping fails the whole Lambda invocation, so batchItemFailures never returns
        # and every message in the batch redelivers — while this row stays `running`,
        # where the claim gate stops redelivery from ever rescuing it.
        crashing = AsyncMock(side_effect=RuntimeError("connection reset"))
        with ExitStack() as stack:
            _, _, fail = _enter(stack, turn=crashing)
            outcome = await _execute(allow_retry=True)
        assert outcome == JobOutcome(status="failed", retryable=False)
        fail.assert_awaited_once()

    async def test_it_is_terminal_even_where_redelivery_exists(self):
        # Retryability is an allowlist of faults known to be transient; an error we
        # cannot classify does not join it by default.
        crashing = AsyncMock(side_effect=RuntimeError("connection reset"))
        with ExitStack() as stack:
            _, _, fail = _enter(stack, turn=crashing)
            await _execute(allow_retry=True)
        assert fail.await_args.kwargs["retryable"] is False

    async def test_the_stored_error_says_nothing_internal(self):
        # `error` is rendered in the chat, and an unhandled exception's text can carry
        # connection strings, row contents or internal paths.
        crashing = AsyncMock(side_effect=RuntimeError("postgres://user:hunter2@db:5432"))
        with ExitStack() as stack:
            _, _, fail = _enter(stack, turn=crashing)
            await _execute(allow_retry=True)
        stored = fail.await_args.kwargs["error"]
        assert stored == UNEXPECTED_FAILURE
        assert "hunter2" not in stored

    async def test_cancellation_still_unwinds(self):
        # BaseException, so shutdown and task cancellation must not be turned into a
        # failed turn — the job is genuinely unfinished and the sweep should own it.
        cancelled = AsyncMock(side_effect=asyncio.CancelledError())
        with ExitStack() as stack:
            _, _, fail = _enter(stack, turn=cancelled)
            with pytest.raises(asyncio.CancelledError):
                await _execute(allow_retry=True)
        fail.assert_not_awaited()

    async def test_a_crashed_turn_stores_no_result(self):
        crashing = AsyncMock(side_effect=RuntimeError("connection reset"))
        with ExitStack() as stack:
            _, complete, _ = _enter(stack, turn=crashing)
            await _execute(allow_retry=True)
        complete.assert_not_awaited()
