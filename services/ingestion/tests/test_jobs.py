"""Tests for /api/v1/jobs endpoints."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.connectors.base import IngestionReport
from app.main import create_app

_TOKEN = "test-service-token"
_AUTH = {"Authorization": f"Bearer {_TOKEN}"}


def _mock_supabase_client():
    """Return a mock async context-manager Supabase client."""
    client = MagicMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    client.rpc.return_value.execute = AsyncMock()
    client.table.return_value.insert.return_value.execute = AsyncMock()
    client.table.return_value.update.return_value.eq.return_value.execute = AsyncMock()
    client.table.return_value.delete.return_value.in_.return_value.execute = AsyncMock()
    client.table.return_value.upsert.return_value.execute = AsyncMock()
    return client


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=create_app()), base_url="http://test"
    ) as ac:
        yield ac


# ---------------------------------------------------------------------------
# POST /api/v1/jobs/process
# ---------------------------------------------------------------------------

class TestProcessNextJob:
    @pytest.mark.asyncio
    async def test_no_pending_jobs_returns_not_processed(self, client):
        mock_sb = _mock_supabase_client()
        mock_sb.rpc.return_value.execute = AsyncMock(return_value=MagicMock(data=[]))

        with patch("app.api.jobs.acreate_client", return_value=mock_sb):
            r = await client.post("/api/v1/jobs/process", headers=_AUTH)

        assert r.status_code == 200
        body = r.json()
        assert body["processed"] is False
        assert "No pending jobs" in body["message"]

    @pytest.mark.asyncio
    async def test_unknown_source_returns_failed(self, client):
        job = {"id": "j-1", "source": "unknown-src", "attempts": 0}
        mock_sb = _mock_supabase_client()

        with patch("app.api.jobs.acreate_client", return_value=mock_sb), \
             patch("app.api.jobs.claim_next_job", new_callable=AsyncMock, return_value=job), \
             patch("app.api.jobs.update_job_status", new_callable=AsyncMock):
            r = await client.post("/api/v1/jobs/process", headers=_AUTH)

        assert r.status_code == 200
        body = r.json()
        assert body["processed"] is True
        assert body["status"] == "failed"

    @pytest.mark.asyncio
    async def test_known_source_runs_connector(self, client):
        job = {"id": "j-2", "source": "loopnet-seed", "attempts": 0}
        mock_sb = _mock_supabase_client()

        report = IngestionReport(source="loopnet-seed", fetched=5, normalized=5)
        mock_connector = AsyncMock(return_value=report)

        with patch("app.api.jobs.acreate_client", return_value=mock_sb), \
             patch("app.api.jobs.claim_next_job", new_callable=AsyncMock, return_value=job), \
             patch("app.api.jobs.update_job_status", new_callable=AsyncMock), \
             patch.dict("app.api.jobs._CONNECTORS", {"loopnet-seed": MagicMock(return_value=MagicMock(run=mock_connector))}):
            r = await client.post("/api/v1/jobs/process", headers=_AUTH)

        assert r.status_code == 200
        assert r.json()["status"] == "done"

    @pytest.mark.asyncio
    async def test_requires_auth_token(self, client):
        r = await client.post("/api/v1/jobs/process")
        assert r.status_code in (401, 403, 503)

    @pytest.mark.asyncio
    async def test_wrong_token_returns_401(self, client):
        r = await client.post("/api/v1/jobs/process", headers={"Authorization": "Bearer wrong"})
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/v1/jobs/run/{source}
# ---------------------------------------------------------------------------

class TestRunJob:
    @pytest.mark.asyncio
    async def test_unknown_source_returns_400(self, client):
        r = await client.post("/api/v1/jobs/run/nonexistent", headers=_AUTH)
        assert r.status_code == 400

    @pytest.mark.asyncio
    async def test_known_source_runs_and_returns_done(self, client):
        job_row = {"id": "j-3", "attempts": 0}
        mock_sb = _mock_supabase_client()

        report = IngestionReport(source="loopnet-seed", fetched=3, normalized=3)
        mock_connector = AsyncMock(return_value=report)

        with patch("app.api.jobs.acreate_client", return_value=mock_sb), \
             patch("app.api.jobs.insert_job_row", new_callable=AsyncMock, return_value=job_row), \
             patch("app.api.jobs.update_job_status", new_callable=AsyncMock), \
             patch.dict("app.api.jobs._CONNECTORS", {"loopnet-seed": MagicMock(return_value=MagicMock(run=mock_connector))}):
            r = await client.post("/api/v1/jobs/run/loopnet-seed", headers=_AUTH)

        assert r.status_code == 200
        assert r.json()["processed"] is True

    @pytest.mark.asyncio
    async def test_requires_auth(self, client):
        r = await client.post("/api/v1/jobs/run/loopnet-seed")
        assert r.status_code in (401, 403, 503)


# ---------------------------------------------------------------------------
# _run_connector retry logic (via private function)
# ---------------------------------------------------------------------------

class TestRunConnectorRetry:
    @pytest.mark.asyncio
    async def test_retries_when_under_attempt_cap(self):
        from app.api.jobs import _run_connector

        mock_client = MagicMock()
        failing_connector = MagicMock(return_value=MagicMock(run=AsyncMock(side_effect=RuntimeError("fail"))))

        with patch("app.api.jobs.update_job_status", new_callable=AsyncMock):
            status = await _run_connector(mock_client, "j-1", "loopnet-seed", 1, failing_connector)

        assert status == "pending"

    @pytest.mark.asyncio
    async def test_fails_permanently_when_at_attempt_cap(self):
        from app.api.jobs import _run_connector, _MAX_ATTEMPTS

        mock_client = MagicMock()
        failing_connector = MagicMock(return_value=MagicMock(run=AsyncMock(side_effect=RuntimeError("fail"))))

        with patch("app.api.jobs.update_job_status", new_callable=AsyncMock):
            status = await _run_connector(mock_client, "j-1", "loopnet-seed", _MAX_ATTEMPTS, failing_connector)

        assert status == "failed"
