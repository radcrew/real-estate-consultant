"""Tests for recording intake turns.

The behaviour that matters is what happens when the write fails. This runs after the
user's answer is already computed, so a failure has to be invisible to them — telemetry
that can turn a working intake turn into a 500 is worse than no telemetry.
"""

from __future__ import annotations

import logging
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from app.repositories.intake_parse_log import record_intake_parse

_SESSION = UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")


def _client(*, fails: bool = False) -> MagicMock:
    client = MagicMock()
    execute = AsyncMock(side_effect=RuntimeError("boom") if fails else None)
    client.table.return_value.insert.return_value.execute = execute
    return client


def _row(client: MagicMock) -> dict:
    return client.table.return_value.insert.call_args.args[0]


async def _record(client, **overrides):
    payload = {
        "session_id": _SESSION,
        "user_input": "a warehouse in Dallas",
        "current_criteria": {"location": "Dallas"},
        "model_output": {"extracted": {"property_type": ["industrial"]}},
        "extracted": {"property_type": ["industrial"]},
        "unconfirmed_fields": [],
        "missing_fields": ["price"],
        "model": "qwen2.5-0.5b-instruct-intake-v6-q4_k_m",
        "temperature": 0.1,
        "latency_ms": 1200,
    }
    payload.update(overrides)
    await record_intake_parse(client, **payload)


class TestWhatGetsWritten:
    async def test_the_turn_is_recorded(self):
        client = _client()
        await _record(client)
        client.table.assert_called_once_with("intake_parse_log")
        assert _row(client)["user_input"] == "a warehouse in Dallas"

    async def test_the_inputs_needed_to_replay_the_turn_are_kept(self):
        """user_input plus current_criteria are exactly an eval turn's inputs."""
        client = _client()
        await _record(client)
        row = _row(client)
        assert row["current_criteria"] == {"location": "Dallas"}
        assert row["session_id"] == str(_SESSION)

    async def test_both_sides_of_the_filters_are_kept(self):
        """Only holding the filtered result cannot say whether the model or a filter
        changed between two runs."""
        client = _client()
        await _record(
            client,
            model_output={"extracted": {"price": {"min": 100000}}},
            extracted={},
        )
        row = _row(client)
        assert row["model_output"] == {"extracted": {"price": {"min": 100000}}}
        assert row["extracted"] == {}

    async def test_the_model_is_recorded(self):
        """A row that cannot be attributed to an adapter cannot compare two."""
        client = _client()
        await _record(client)
        assert _row(client)["model"] == "qwen2.5-0.5b-instruct-intake-v6-q4_k_m"

    async def test_a_session_less_turn_is_still_recorded(self):
        client = _client()
        await _record(client, session_id=None)
        assert _row(client)["session_id"] is None

    @pytest.mark.parametrize("blank", ["", "   ", "\n"])
    async def test_an_empty_message_is_not_a_turn(self, blank):
        client = _client()
        await _record(client, user_input=blank)
        client.table.assert_not_called()

    async def test_a_pasted_document_is_clipped_and_says_so(self):
        client = _client()
        await _record(client, user_input="x" * 10_000)
        stored = _row(client)["user_input"]
        assert len(stored) == 4000
        assert stored.endswith("...[truncated]")

    async def test_a_message_at_the_limit_is_untouched(self):
        client = _client()
        await _record(client, user_input="x" * 4000)
        assert _row(client)["user_input"] == "x" * 4000


class TestFailureIsInvisible:
    async def test_a_failed_write_does_not_raise(self):
        """The table may not be migrated yet, and the answer is already computed."""
        await _record(_client(fails=True))

    async def test_a_failed_write_is_logged(self, caplog):
        with caplog.at_level(logging.WARNING):
            await _record(_client(fails=True))
        assert "intake_parse_log" in caplog.text
