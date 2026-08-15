"""Tests for job result delivery: poll endpoint and SSE stream."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.intake_sessions.jobs import job_event_stream, sse_frame
from app.schemas.intake_sessions import IntakeJobStatusResponse

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


def _frames(chunks: list[str]) -> list[dict]:
    """Parse the ``data:`` payload out of each SSE frame."""
    return [
        json.loads(line[len("data: ") :])
        for chunk in chunks
        for line in chunk.splitlines()
        if line.startswith("data: ")
    ]


class TestSseFrame:
    def test_frames_end_with_a_blank_line(self):
        """Without the terminating blank line an EventSource never dispatches."""
        payload = IntakeJobStatusResponse(job_id=_JOB_UUID, status="queued")
        assert sse_frame(payload).endswith("\n\n")

    def test_named_events_carry_their_name(self):
        payload = IntakeJobStatusResponse(job_id=_JOB_UUID, status="running")
        assert sse_frame(payload, event="timeout").startswith("event: timeout\n")


class TestPollEndpoint:
    async def test_returns_the_job_state(self, client):
        with patch(
            f"{_JOBS}.get_intake_job_row",
            new_callable=AsyncMock,
            return_value=_row("succeeded", result=_TURN_RESULT),
        ):
            r = await client.get(
                f"/api/v1/intake-sessions/{_SESSION_UUID}/jobs/{_JOB_UUID}"
            )
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "succeeded"
        assert body["result"]["extracted"] == {"location": "Austin"}

    async def test_unknown_job_is_404(self, client):
        with patch(
            f"{_JOBS}.get_intake_job_row",
            new_callable=AsyncMock,
            side_effect=HTTPException(status_code=404, detail="Intake job not found."),
        ):
            r = await client.get(
                f"/api/v1/intake-sessions/{_SESSION_UUID}/jobs/{_JOB_UUID}"
            )
        assert r.status_code == 404

    async def test_a_failed_job_reports_its_error(self, client):
        with patch(
            f"{_JOBS}.get_intake_job_row",
            new_callable=AsyncMock,
            return_value=_row("failed", error="The assistant's reply didn't come through."),
        ):
            r = await client.get(
                f"/api/v1/intake-sessions/{_SESSION_UUID}/jobs/{_JOB_UUID}"
            )
        assert r.json()["error"] == "The assistant's reply didn't come through."


class TestStreamEndpoint:
    async def test_unknown_job_404s_before_the_stream_opens(self, client):
        """Raising inside the generator would be too late — the client would get a 200
        that simply stops."""
        with patch(
            f"{_JOBS}.get_intake_job_row",
            new_callable=AsyncMock,
            side_effect=HTTPException(status_code=404, detail="Intake job not found."),
        ):
            r = await client.get(
                f"/api/v1/intake-sessions/{_SESSION_UUID}/jobs/{_JOB_UUID}/stream"
            )
        assert r.status_code == 404

    async def test_streams_until_the_job_settles(self, client):
        rows = [_row("queued"), _row("running"), _row("succeeded", result=_TURN_RESULT)]
        with (
            patch(f"{_JOBS}.get_intake_job_row", new_callable=AsyncMock, side_effect=rows * 2),
            patch(f"{_JOBS}.settings") as cfg,
        ):
            cfg.chat_job_timeout_seconds = 5.0
            cfg.chat_job_poll_interval_seconds = 0.0
            r = await client.get(
                f"/api/v1/intake-sessions/{_SESSION_UUID}/jobs/{_JOB_UUID}/stream"
            )
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/event-stream")
        frames = _frames([r.text])
        assert [f["status"] for f in frames] == ["running", "succeeded"]

    async def test_proxy_buffering_is_disabled(self, client):
        """A buffering proxy would hold every frame until the response ends."""
        with (
            patch(
                f"{_JOBS}.get_intake_job_row",
                new_callable=AsyncMock,
                return_value=_row("succeeded", result=_TURN_RESULT),
            ),
            patch(f"{_JOBS}.settings") as cfg,
        ):
            cfg.chat_job_timeout_seconds = 5.0
            cfg.chat_job_poll_interval_seconds = 0.0
            r = await client.get(
                f"/api/v1/intake-sessions/{_SESSION_UUID}/jobs/{_JOB_UUID}/stream"
            )
        assert r.headers["x-accel-buffering"] == "no"
        assert r.headers["cache-control"] == "no-cache"


class TestStreamAdmission:
    async def test_an_exhausted_budget_refuses_the_stream(self, client, monkeypatch):
        """Wiring test. Streams are anonymous and each holds a serverless function, so
        without this one valid job id could be opened without limit."""
        from app.core import intake_admission as module
        from app.core.intake_admission import IntakeAdmissionControl

        monkeypatch.setattr(
            module,
            "intake_admission",
            IntakeAdmissionControl(ip_per_minute=1, session_per_minute=10),
        )
        with (
            patch(
                f"{_JOBS}.get_intake_job_row",
                new_callable=AsyncMock,
                return_value=_row("succeeded", result=_TURN_RESULT),
            ),
            patch(f"{_JOBS}.settings") as cfg,
        ):
            cfg.chat_job_timeout_seconds = 5.0
            cfg.chat_job_poll_interval_seconds = 0.0
            url = f"/api/v1/intake-sessions/{_SESSION_UUID}/jobs/{_JOB_UUID}/stream"
            first = await client.get(url)
            second = await client.get(url)
        assert first.status_code == 200
        assert second.status_code == 429

    async def test_polling_stays_unmetered(self, client, monkeypatch):
        """It runs once a second by design, so any budget tight enough to protect the
        stream would break the fallback that exists for when the stream fails."""
        from app.core import intake_admission as module
        from app.core.intake_admission import IntakeAdmissionControl

        monkeypatch.setattr(
            module,
            "intake_admission",
            IntakeAdmissionControl(ip_per_minute=1, session_per_minute=1),
        )
        with patch(
            f"{_JOBS}.get_intake_job_row",
            new_callable=AsyncMock,
            return_value=_row("running"),
        ):
            url = f"/api/v1/intake-sessions/{_SESSION_UUID}/jobs/{_JOB_UUID}"
            for _ in range(4):
                assert (await client.get(url)).status_code == 200


class TestJobEventStream:
    async def test_stops_on_a_terminal_status(self):
        get_row = AsyncMock(return_value=_row("failed", error="nope"))
        with patch(f"{_JOBS}.get_intake_job_row", get_row):
            chunks = [
                chunk
                async for chunk in job_event_stream(
                    MagicMock(),
                    session_id=_SESSION_UUID,
                    job_id=_JOB_UUID,
                    timeout_seconds=5.0,
                    poll_interval=0.0,
                )
            ]
        assert len(chunks) == 1
        assert get_row.await_count == 1

    async def test_gives_up_at_the_deadline_with_a_named_event(self):
        """The job may still finish, so the client is told to fall back, not that it
        failed — polling can still pick up the result."""
        get_row = AsyncMock(return_value=_row("running"))
        with patch(f"{_JOBS}.get_intake_job_row", get_row):
            chunks = [
                chunk
                async for chunk in job_event_stream(
                    MagicMock(),
                    session_id=_SESSION_UUID,
                    job_id=_JOB_UUID,
                    timeout_seconds=0.0,
                    poll_interval=0.0,
                )
            ]
        assert "event: timeout" in chunks[-1]
        assert _frames(chunks)[-1]["status"] == "running"

    @pytest.mark.parametrize("status", ["succeeded", "failed"])
    async def test_terminal_statuses_end_the_stream(self, status):
        with patch(
            f"{_JOBS}.get_intake_job_row", new_callable=AsyncMock, return_value=_row(status)
        ):
            chunks = [
                chunk
                async for chunk in job_event_stream(
                    MagicMock(),
                    session_id=_SESSION_UUID,
                    job_id=_JOB_UUID,
                    timeout_seconds=5.0,
                    poll_interval=0.0,
                )
            ]
        assert len(chunks) == 1
