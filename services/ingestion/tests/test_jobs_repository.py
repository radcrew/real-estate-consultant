"""Tests for app.repositories.jobs — direct Supabase query behavior."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.repositories.jobs import claim_next_job, insert_job_row, update_job_status


def _mock_client():
    client = MagicMock()
    client.rpc.return_value.execute = AsyncMock()
    client.table.return_value.insert.return_value.execute = AsyncMock()
    client.table.return_value.update.return_value.eq.return_value.execute = AsyncMock()
    return client


class TestClaimNextJob:
    @pytest.mark.asyncio
    async def test_returns_row_when_a_job_is_claimed(self):
        client = _mock_client()
        job = {"id": "j-1", "source": "loopnet-seed", "attempts": 0}
        client.rpc.return_value.execute = AsyncMock(return_value=MagicMock(data=[job]))

        result = await claim_next_job(client)
        assert result == job

    @pytest.mark.asyncio
    async def test_returns_none_when_nothing_pending(self):
        client = _mock_client()
        client.rpc.return_value.execute = AsyncMock(return_value=MagicMock(data=[]))

        result = await claim_next_job(client)
        assert result is None


class TestInsertJobRow:
    @pytest.mark.asyncio
    async def test_returns_inserted_row(self):
        client = _mock_client()
        job = {"id": "j-2", "source": "loopnet-seed", "attempts": 0}
        client.table.return_value.insert.return_value.execute = AsyncMock(
            return_value=MagicMock(data=[job]),
        )

        result = await insert_job_row(client, "loopnet-seed")
        assert result == job
        client.table.return_value.insert.assert_called_once_with({"source": "loopnet-seed"})

    @pytest.mark.asyncio
    async def test_raises_502_when_insert_returns_no_data(self):
        client = _mock_client()
        client.table.return_value.insert.return_value.execute = AsyncMock(
            return_value=MagicMock(data=[]),
        )

        with pytest.raises(HTTPException) as info:
            await insert_job_row(client, "loopnet-seed")
        assert info.value.status_code == 502


class TestUpdateJobStatus:
    @pytest.mark.asyncio
    async def test_sends_status_only_by_default(self):
        client = _mock_client()
        await update_job_status(client, "j-3", "failed")
        client.table.return_value.update.assert_called_once_with({"status": "failed"})

    @pytest.mark.asyncio
    async def test_includes_result_when_given(self):
        client = _mock_client()
        result = {"fetched": 5, "normalized": 5}
        await update_job_status(client, "j-3", "done", result=result)
        client.table.return_value.update.assert_called_once_with(
            {"status": "done", "result": result},
        )

    @pytest.mark.asyncio
    async def test_includes_error_when_given(self):
        client = _mock_client()
        await update_job_status(client, "j-3", "failed", error="boom")
        client.table.return_value.update.assert_called_once_with(
            {"status": "failed", "error": "boom"},
        )

    @pytest.mark.asyncio
    async def test_filters_by_job_id(self):
        client = _mock_client()
        await update_job_status(client, "j-3", "failed")
        client.table.return_value.update.return_value.eq.assert_called_once_with("id", "j-3")
