"""Tests for job result delivery.

The client polls this route. An SSE endpoint lived here and was removed: these routes
require a bearer token and ``EventSource`` cannot send one, so every browser connection
401'd — which these tests could not have caught, since the API fixture overrides
``get_current_user``.
"""
from __future__ import annotations

from contextlib import ExitStack
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

_SESSION_UUID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
_JOB_UUID = "11111111-2222-3333-4444-555555555555"
_JOBS = "app.api.v1.endpoints.intake_sessions.jobs"

_TURN_RESULT = {
    "extracted": {"location": "Austin"},
    "criteria": {"location": "Austin"},
    "current_index": 1,
    "total_questions": 2,
    "missing_fields": ["property_type"],
    "next_question": None,
    "is_complete": False,
}


def _row(status: str = "queued", **extra):
    return {"id": _JOB_UUID, "session_id": _SESSION_UUID, "status": status, **extra}


def _url() -> str:
    return f"/api/v1/intake-sessions/{_SESSION_UUID}/jobs/{_JOB_UUID}"


def _owns_session(**overrides):
    """The caller owns the session. Scoping the job by session alone is not enough."""
    return patch(
        f"{_JOBS}.get_owned_intake_session_row",
        new_callable=AsyncMock,
        **({"return_value": {"id": _SESSION_UUID}} | overrides),
    )


def _job(**overrides):
    return patch(f"{_JOBS}.get_intake_job_row", new_callable=AsyncMock, **overrides)


class TestPollEndpoint:
    async def test_returns_the_job_state(self, client):
        with ExitStack() as stack:
            stack.enter_context(_owns_session())
            stack.enter_context(_job(return_value=_row("succeeded", result=_TURN_RESULT)))
            r = await client.get(_url())
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "succeeded"
        assert body["result"]["extracted"] == {"location": "Austin"}

    async def test_unknown_job_is_404(self, client):
        with ExitStack() as stack:
            stack.enter_context(_owns_session())
            stack.enter_context(
                _job(side_effect=HTTPException(status_code=404, detail="Intake job not found."))
            )
            r = await client.get(_url())
        assert r.status_code == 404

    async def test_another_users_session_is_404_and_reads_no_job(self, client):
        """A job's result holds the criteria extracted from someone's message, so two
        guessed UUIDs must not be enough to read it."""
        with ExitStack() as stack:
            stack.enter_context(
                _owns_session(
                    return_value=None,
                    side_effect=HTTPException(
                        status_code=404, detail="Intake session not found."
                    ),
                )
            )
            job = stack.enter_context(_job(return_value=_row("succeeded")))
            r = await client.get(_url())
        assert r.status_code == 404
        job.assert_not_awaited()

    async def test_a_failed_job_reports_its_error(self, client):
        with ExitStack() as stack:
            stack.enter_context(_owns_session())
            stack.enter_context(
                _job(
                    return_value=_row(
                        "failed", error="The assistant's reply didn't come through."
                    )
                )
            )
            r = await client.get(_url())
        assert r.json()["error"] == "The assistant's reply didn't come through."

    async def test_a_running_job_carries_no_result_yet(self, client):
        with ExitStack() as stack:
            stack.enter_context(_owns_session())
            stack.enter_context(_job(return_value=_row("running")))
            r = await client.get(_url())
        assert r.json() == {
            "job_id": _JOB_UUID,
            "status": "running",
            "result": None,
            "error": None,
        }

    async def test_polling_is_unmetered(self, client, monkeypatch):
        """The client asks about once a second while a turn runs, so any budget tight
        enough to matter would break delivery itself."""
        from app.core import intake_admission as module
        from app.core.intake_admission import IntakeAdmissionControl

        monkeypatch.setattr(
            module,
            "intake_admission",
            IntakeAdmissionControl(ip_per_minute=1, session_per_minute=1),
        )
        with ExitStack() as stack:
            stack.enter_context(_owns_session())
            stack.enter_context(_job(return_value=_row("running")))
            for _ in range(4):
                assert (await client.get(_url())).status_code == 200
