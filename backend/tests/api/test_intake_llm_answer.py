"""Tests for POST /intake-sessions/{id}/answers/llm.

The endpoint no longer returns the turn: it accepts one, durably, and hands back a job to
follow. That is the point — the user's text survives a provider stall, which it did not
when the turn ran inside the request.
"""
from __future__ import annotations

from contextlib import ExitStack
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException

from app.clients.bedrock_guardrail import GuardrailOutcome

_SESSION_UUID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
_JOB_UUID = "11111111-2222-3333-4444-555555555555"

_ENDPOINT = "app.api.v1.endpoints.intake_sessions.answers.llm"
_JOB_SERVICE = "app.services.intake_jobs"

_SESSION_ROW = {
    "id": _SESSION_UUID,
    "status": "in_progress",
    "search_profile_id": None,
    "criteria": {},
}

_JOB_ROW = {"id": _JOB_UUID, "session_id": _SESSION_UUID, "status": "queued"}


def _turn_response():
    response = MagicMock()
    response.model_dump.return_value = {"is_complete": False}
    return response


def _enter(
    stack,
    *,
    active_jobs: int = 0,
    queue_enabled: bool = False,
    turn=None,
    publish=None,
    screen=None,
):
    """Patch the endpoint's collaborators, leaving its own decisions under test."""
    queue = MagicMock()
    queue.enabled = queue_enabled
    queue.publish = publish or AsyncMock(return_value="msg-1")
    guardrail = MagicMock()
    guardrail.screen = screen or AsyncMock(
        side_effect=lambda text, **_: GuardrailOutcome(text=text, blocked=False)
    )
    stack.enter_context(patch(f"{_ENDPOINT}.bedrock_guardrail", guardrail))
    run = turn or AsyncMock(return_value=_turn_response())
    complete = AsyncMock(return_value={})
    fail = AsyncMock(return_value={})
    for item in (
        patch(
            f"{_ENDPOINT}.get_intake_session_row",
            new_callable=AsyncMock,
            return_value=_SESSION_ROW,
        ),
        patch(
            f"{_ENDPOINT}.count_active_intake_jobs",
            new_callable=AsyncMock,
            return_value=active_jobs,
        ),
        patch(f"{_ENDPOINT}.expire_stale_running_jobs", new_callable=AsyncMock, return_value=[]),
        patch(
            f"{_ENDPOINT}.expire_abandoned_queued_jobs",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(f"{_ENDPOINT}.create_intake_job", new_callable=AsyncMock, return_value=_JOB_ROW),
        patch(f"{_ENDPOINT}.claim_intake_job", new_callable=AsyncMock, return_value=_JOB_ROW),
        patch(f"{_ENDPOINT}.chat_job_queue", queue),
        patch(f"{_JOB_SERVICE}.run_llm_intake_turn", run),
        patch(f"{_JOB_SERVICE}.complete_intake_job", complete),
        patch(f"{_JOB_SERVICE}.fail_intake_job", fail),
    ):
        stack.enter_context(item)
    return queue, run, complete, fail


async def _post(client, text: str = "warehouse in Austin"):
    return await client.post(
        f"/api/v1/intake-sessions/{_SESSION_UUID}/answers/llm",
        json={"input": text},
    )


class TestEnqueue:
    async def test_returns_202_with_a_job_to_follow(self, client):
        with ExitStack() as stack:
            _enter(stack, queue_enabled=True)
            r = await _post(client)
        assert r.status_code == 202
        assert r.json() == {"job_id": _JOB_UUID, "status": "queued"}

    async def test_the_turn_is_not_run_in_the_request(self, client):
        """A provider stall must not become a 5xx that loses what the user typed."""
        with ExitStack() as stack:
            queue, run, _, _ = _enter(stack, queue_enabled=True)
            await _post(client)
        run.assert_not_awaited()
        assert queue.publish.await_count == 1

    async def test_the_row_exists_before_the_message(self, client):
        """A row with no message is redrivable; a message with no row is undiagnosable."""
        order: list[str] = []
        create = AsyncMock(side_effect=lambda *a, **k: order.append("row") or _JOB_ROW)
        publish = AsyncMock(side_effect=lambda **k: order.append("publish"))
        with ExitStack() as stack:
            _enter(stack, queue_enabled=True, publish=publish)
            stack.enter_context(patch(f"{_ENDPOINT}.create_intake_job", create))
            await _post(client)
        assert order == ["row", "publish"]

    async def test_a_failed_publish_surfaces_as_503(self, client):
        publish = AsyncMock(side_effect=HTTPException(status_code=503, detail="no queue"))
        with ExitStack() as stack:
            _enter(stack, queue_enabled=True, publish=publish)
            r = await _post(client)
        assert r.status_code == 503

    async def test_missing_session_is_404(self, client):
        with ExitStack() as stack:
            _enter(stack, queue_enabled=True)
            stack.enter_context(
                patch(
                    f"{_ENDPOINT}.get_intake_session_row",
                    new_callable=AsyncMock,
                    side_effect=HTTPException(status_code=404, detail="Intake session not found."),
                )
            )
            r = await _post(client)
        assert r.status_code == 404

    async def test_one_turn_at_a_time_per_session(self, client):
        """FIFO already serialises a session's turns; a second in flight only queues."""
        with ExitStack() as stack:
            _enter(stack, queue_enabled=True, active_jobs=1)
            r = await _post(client)
        assert r.status_code == 429

    async def test_dead_rows_are_swept_before_the_in_flight_count(self, client):
        """A worker killed mid-turn leaves a claimed row redelivery cannot finish. Left
        alone it holds the session's only slot, locking the user out of their own
        conversation — so the sweep has to run before the count, not after."""
        order: list[str] = []
        expire_running = AsyncMock(side_effect=lambda *a, **k: order.append("running") or [])
        expire_queued = AsyncMock(side_effect=lambda *a, **k: order.append("queued") or [])
        count = AsyncMock(side_effect=lambda *a, **k: order.append("count") or 0)
        with ExitStack() as stack:
            _enter(stack, queue_enabled=True)
            stack.enter_context(patch(f"{_ENDPOINT}.expire_stale_running_jobs", expire_running))
            stack.enter_context(
                patch(f"{_ENDPOINT}.expire_abandoned_queued_jobs", expire_queued)
            )
            stack.enter_context(patch(f"{_ENDPOINT}.count_active_intake_jobs", count))
            r = await _post(client)
        assert r.status_code == 202
        # Both unfinished states are swept: the in-flight cap counts queued and running
        # alike, so clearing only one still leaves the session lockable.
        assert order == ["running", "queued", "count"]

    async def test_the_queued_sweep_clears_a_redelivery_gap(self):
        """The window measures untouched time, so it only has to clear the gap between
        redelivery attempts — one visibility timeout (180s) — since each attempt moves
        updated_at. It must also outlast the running sweep, which answers a shorter
        question: whether a claimed turn is still being worked on.

        The *ceiling* is the client's patience (`JOB_DEADLINE_MS` in the frontend) and is
        deliberately not asserted against `chat_job_timeout_seconds`: that bounds a single
        SSE connection, which the platform usually cuts short, and tying the sweep to it
        would start expiring live jobs the moment someone shortened the stream.
        """
        from app.core.config import settings as live_settings

        assert live_settings.chat_job_abandoned_after_seconds > 360
        assert (
            live_settings.chat_job_abandoned_after_seconds
            > live_settings.chat_job_stale_after_seconds
        )
        # The running sweep is the last link of the timeout chain, so it has to clear the
        # visibility timeout it sits behind (360s) — and therefore the function timeout
        # and the worst-case provider call underneath that.
        assert live_settings.chat_job_stale_after_seconds > 360


class TestQueueDisabled:
    async def test_same_contract_without_a_queue(self, client):
        """Local dev and CI need no queue, so this path cannot be allowed to rot."""
        with ExitStack() as stack:
            queue, run, complete, _ = _enter(stack, queue_enabled=False)
            r = await _post(client)
        assert r.status_code == 202
        assert r.json() == {"job_id": _JOB_UUID, "status": "succeeded"}
        queue.publish.assert_not_awaited()
        assert run.await_count == 1
        assert complete.await_count == 1

    async def test_a_transient_fault_still_ends_the_job(self, client):
        """Nothing would redeliver it, so leaving it queued would strand it forever."""
        failing = AsyncMock(side_effect=HTTPException(status_code=503, detail="busy"))
        with ExitStack() as stack:
            _, _, _, fail = _enter(stack, queue_enabled=False, turn=failing)
            r = await _post(client)
        assert r.status_code == 202
        assert r.json()["status"] == "failed"
        assert fail.await_args.kwargs["retryable"] is False


class TestGuardrail:
    async def test_the_stored_text_is_the_screened_one(self, client):
        """Screening has to precede the write: the row is what the worker replays, so
        redacting later would mean the raw text had already been persisted."""
        create = AsyncMock(return_value=_JOB_ROW)
        screen = AsyncMock(return_value=GuardrailOutcome(text="my address is {PII}", blocked=False))
        with ExitStack() as stack:
            _enter(stack, queue_enabled=True, screen=screen)
            stack.enter_context(patch(f"{_ENDPOINT}.create_intake_job", create))
            r = await _post(client, "my address is 1 Main St")
        assert r.status_code == 202
        assert create.await_args.kwargs["user_input"] == "my address is {PII}"

    async def test_blocked_text_is_refused_before_a_job_exists(self, client):
        create = AsyncMock(return_value=_JOB_ROW)
        screen = AsyncMock(return_value=GuardrailOutcome(text="disallowed", blocked=True))
        with ExitStack() as stack:
            _enter(stack, queue_enabled=True, screen=screen)
            stack.enter_context(patch(f"{_ENDPOINT}.create_intake_job", create))
            r = await _post(client, "disallowed")
        assert r.status_code == 422
        create.assert_not_awaited()

    async def test_the_inline_path_runs_the_screened_text_too(self, client):
        screen = AsyncMock(return_value=GuardrailOutcome(text="redacted", blocked=False))
        with ExitStack() as stack:
            _, run, _, _ = _enter(stack, queue_enabled=False, screen=screen)
            await _post(client, "my address is 1 Main St")
        assert run.await_args.kwargs["user_input"] == "redacted"


class TestValidation:
    async def test_missing_input_returns_422(self, client):
        r = await client.post(
            f"/api/v1/intake-sessions/{_SESSION_UUID}/answers/llm",
            json={},
        )
        assert r.status_code == 422


class TestAdmissionControl:
    async def test_exhausted_budget_returns_429_without_creating_a_job(
        self, client, monkeypatch
    ):
        """The endpoint is anonymous, so the limiter is the only gate — and a 429 that
        still enqueued work would protect nothing."""
        from app.core import intake_admission as module
        from app.core.intake_admission import IntakeAdmissionControl

        monkeypatch.setattr(
            module,
            "intake_admission",
            IntakeAdmissionControl(ip_per_minute=1, session_per_minute=1),
        )
        create = AsyncMock(return_value=_JOB_ROW)
        with ExitStack() as stack:
            _enter(stack, queue_enabled=True)
            stack.enter_context(patch(f"{_ENDPOINT}.create_intake_job", create))
            first = await _post(client)
            second = await _post(client, "actually, Dallas")

        assert first.status_code == 202
        assert second.status_code == 429
        assert second.headers["retry-after"] == "60"
        assert create.await_count == 1
