"""Tests for the queued intake-turn worker."""
from __future__ import annotations

import asyncio
import json
from contextlib import ExitStack
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import HTTPException

from app.workers import chat_job_worker
from app.workers.chat_job_worker import group_of, parse_record, process_batch

_WORKER = "app.workers.chat_job_worker"
_SERVICE = "app.services.intake_jobs"
_SESSION_A = uuid4()
_SESSION_B = uuid4()


def _record(*, job_id=None, session_id=_SESSION_A, message_id="m-1", body=None) -> dict:
    return {
        "messageId": message_id,
        "body": body
        if body is not None
        else json.dumps(
            {"job_id": str(job_id or uuid4()), "session_id": str(session_id)}
        ),
        "attributes": {"MessageGroupId": str(session_id)},
    }


def _turn_response():
    response = MagicMock()
    response.model_dump.return_value = {"is_complete": False}
    return response


def _enter(
    stack,
    *,
    claimed=None,
    turn=None,
):
    """Patch the worker's collaborators; returns the mocks worth asserting on."""
    claim = AsyncMock(
        return_value=claimed if claimed is not None else {"input": "warehouse in Austin"}
    )
    run = AsyncMock(return_value=_turn_response()) if turn is None else turn
    complete = AsyncMock(return_value={})
    fail = AsyncMock(return_value={})
    # The turn itself runs in the shared job service, which the endpoint's inline path
    # also uses — patching it here keeps both callers exercising the same code.
    for item in (
        patch(f"{_WORKER}.get_client", AsyncMock(return_value=MagicMock())),
        patch(f"{_WORKER}.claim_intake_job", claim),
        patch(f"{_SERVICE}.run_llm_intake_turn", run),
        patch(f"{_SERVICE}.complete_intake_job", complete),
        patch(f"{_SERVICE}.fail_intake_job", fail),
    ):
        stack.enter_context(item)
    return claim, run, complete, fail


class TestParseRecord:
    def test_reads_the_ids(self):
        job_id, session_id = uuid4(), uuid4()
        parsed = parse_record(
            {"body": json.dumps({"job_id": str(job_id), "session_id": str(session_id)})}
        )
        assert parsed == (job_id, session_id)

    @pytest.mark.parametrize(
        "body",
        [
            "not json",
            "",
            json.dumps({"job_id": "x"}),
            json.dumps({"job_id": "nope", "session_id": "y"}),
        ],
    )
    def test_unreadable_bodies_return_none(self, body):
        assert parse_record({"body": body}) is None

    def test_group_defaults_to_empty(self):
        assert group_of({}) == ""


class TestProcessBatch:
    async def test_successful_turn_reports_no_failures(self):
        with ExitStack() as stack:
            _, run, complete, _ = _enter(stack)
            result = await process_batch({"Records": [_record()]})
        assert result == {"batchItemFailures": []}
        assert run.await_count == 1
        assert complete.await_count == 1

    async def test_result_is_stored_as_json_safe_values(self):
        with ExitStack() as stack:
            _, _, complete, _ = _enter(stack)
            await process_batch({"Records": [_record()]})
        assert complete.await_args.kwargs["result_payload"] == {"is_complete": False}

    async def test_the_stored_input_is_what_gets_replayed(self):
        """The row is the source of truth; the message carries only ids."""
        with ExitStack() as stack:
            _, run, _, _ = _enter(stack, claimed={"input": "office in Dallas"})
            await process_batch({"Records": [_record()]})
        assert run.await_args.kwargs["user_input"] == "office in Dallas"

    async def test_an_already_claimed_job_is_dropped(self):
        """A redelivery of finished work must not re-run — or re-bill — the turn."""
        with ExitStack() as stack:
            _, run, complete, fail = _enter(stack, claimed=False)
            claim = AsyncMock(return_value=None)
            stack.enter_context(patch(f"{_WORKER}.claim_intake_job", claim))
            result = await process_batch({"Records": [_record()]})
        assert result == {"batchItemFailures": []}
        run.assert_not_awaited()
        complete.assert_not_awaited()
        fail.assert_not_awaited()

    async def test_unreadable_message_is_not_retried(self):
        """Redelivery cannot fix a malformed body; it would only burn receives."""
        with ExitStack() as stack:
            claim, run, _, _ = _enter(stack)
            result = await process_batch({"Records": [_record(body="not json")]})
        assert result == {"batchItemFailures": []}
        claim.assert_not_awaited()
        run.assert_not_awaited()

    @pytest.mark.parametrize("status", [503, 504])
    async def test_transient_failures_go_back_on_the_queue(self, status):
        failing = AsyncMock(side_effect=HTTPException(status_code=status, detail="busy"))
        with ExitStack() as stack:
            _, _, _, fail = _enter(stack, turn=failing)
            result = await process_batch({"Records": [_record(message_id="m-9")]})
        assert result == {"batchItemFailures": [{"itemIdentifier": "m-9"}]}
        assert fail.await_args.kwargs["retryable"] is True

    @pytest.mark.parametrize("status", [400, 404, 502])
    async def test_deterministic_failures_stop(self, status):
        """Redelivering a refusal or parse failure re-earns the same error at full cost."""
        failing = AsyncMock(side_effect=HTTPException(status_code=status, detail="nope"))
        with ExitStack() as stack:
            _, _, _, fail = _enter(stack, turn=failing)
            result = await process_batch({"Records": [_record()]})
        assert result == {"batchItemFailures": []}
        assert fail.await_args.kwargs["retryable"] is False


class TestFifoOrdering:
    async def test_a_retry_blocks_later_turns_of_the_same_session(self):
        """The FIFO obligation: deleting the later message would let turn 2 apply while
        turn 1 is still being retried, merging the conversation out of order."""
        failing = AsyncMock(side_effect=HTTPException(status_code=503, detail="busy"))
        with ExitStack() as stack:
            _, run, _, _ = _enter(stack, turn=failing)
            result = await process_batch(
                {
                    "Records": [
                        _record(message_id="m-1", session_id=_SESSION_A),
                        _record(message_id="m-2", session_id=_SESSION_A),
                    ]
                }
            )
        assert result == {
            "batchItemFailures": [{"itemIdentifier": "m-1"}, {"itemIdentifier": "m-2"}]
        }
        # The second turn was never attempted, so it cannot land before the first.
        assert run.await_count == 1

    async def test_other_sessions_are_unaffected(self):
        """Groups are independent — one stalled conversation must not block the rest."""
        calls: list[UUID] = []

        async def _run(client, *, session_id, user_input):
            calls.append(session_id)
            if session_id == _SESSION_A:
                raise HTTPException(status_code=503, detail="busy")
            return _turn_response()

        with ExitStack() as stack:
            _enter(stack, turn=AsyncMock(side_effect=_run))
            result = await process_batch(
                {
                    "Records": [
                        _record(message_id="m-1", session_id=_SESSION_A),
                        _record(message_id="m-2", session_id=_SESSION_B),
                    ]
                }
            )
        assert result == {"batchItemFailures": [{"itemIdentifier": "m-1"}]}
        assert calls == [_SESSION_A, _SESSION_B]

    async def test_a_terminal_failure_does_not_block_the_session(self):
        """That turn is finished, unsuccessfully. The next one should still run."""
        seen: list[str] = []

        async def _run(client, *, session_id, user_input):
            seen.append(user_input)
            if len(seen) == 1:
                raise HTTPException(status_code=502, detail="bad reply")
            return _turn_response()

        with ExitStack() as stack:
            _enter(stack, turn=AsyncMock(side_effect=_run))
            result = await process_batch(
                {
                    "Records": [
                        _record(message_id="m-1", session_id=_SESSION_A),
                        _record(message_id="m-2", session_id=_SESSION_A),
                    ]
                }
            )
        assert result == {"batchItemFailures": []}
        assert len(seen) == 2


class TestHandler:
    def test_handler_runs_the_batch(self):
        with ExitStack() as stack:
            _enter(stack)
            result = chat_job_worker.handler({"Records": [_record()]}, None)
        assert result == {"batchItemFailures": []}

    def test_the_loop_survives_repeated_invocations(self):
        """Lambda reuses a warm container, and ``asyncio.run`` closes its loop on return —
        so a module-scope client bound to that loop breaks on the *second* call. Every
        first invocation succeeded, which is why this read as an intermittent fault.

        The stub below stands in for the Supabase client by holding onto the loop that
        created it, so a regression to ``asyncio.run`` fails here rather than in
        production. Mocks that ignore the loop would pass either way.
        """
        seen: dict[str, asyncio.AbstractEventLoop] = {}

        async def client_bound_to_its_loop():
            first_loop = seen.setdefault("loop", asyncio.get_running_loop())
            if first_loop.is_closed():
                raise RuntimeError("Event loop is closed")
            return MagicMock()

        with ExitStack() as stack:
            _enter(stack)
            stack.enter_context(patch(f"{_WORKER}.get_client", client_bound_to_its_loop))
            first = chat_job_worker.handler({"Records": [_record(message_id="m-1")]}, None)
            second = chat_job_worker.handler({"Records": [_record(message_id="m-2")]}, None)
            third = chat_job_worker.handler({"Records": [_record(message_id="m-3")]}, None)

        assert first == second == third == {"batchItemFailures": []}
        assert not chat_job_worker.event_loop().is_closed()

    def test_a_closed_loop_is_replaced_and_clears_the_client_cache(self):
        """Anything cached against a dead loop is dead too, so they reset together."""
        chat_job_worker.event_loop().close()
        chat_job_worker._initialised = True

        with ExitStack() as stack:
            _enter(stack)
            result = chat_job_worker.handler({"Records": [_record()]}, None)

        assert result == {"batchItemFailures": []}
        assert not chat_job_worker.event_loop().is_closed()
