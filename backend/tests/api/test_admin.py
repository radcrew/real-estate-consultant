"""Tests for admin endpoints."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.core.deps import get_current_admin


@pytest.fixture
async def admin_client(mock_db, mock_supabase, mock_user):
    """Client with admin override."""
    from httpx import ASGITransport, AsyncClient
    from app.core.database import get_session
    from app.core.supabase_sdk import get_supabase_sdk_client
    from app.core.deps import get_current_user
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[get_session] = lambda: mock_db
    app.dependency_overrides[get_supabase_sdk_client] = lambda: mock_supabase
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_current_admin] = lambda: mock_user
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


_JOB_ROW = {"id": "job-uuid-1", "source": "loopnet-seed", "status": "pending", "idempotency_key": "loopnet-seed:2026-06-17"}


class TestEnqueueIngest:
    async def test_success_enqueues_job(self, admin_client, mock_supabase):
        no_existing = MagicMock()
        no_existing.data = []
        inserted = MagicMock()
        inserted.data = [_JOB_ROW]

        with patch("app.api.v1.endpoints.admin.router.execute_db_safe", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = [no_existing, inserted]
            with patch("app.api.v1.endpoints.admin.router.wake_processor", new_callable=AsyncMock):
                r = await admin_client.post("/api/v1/admin/ingest", json={"source": "loopnet-seed"})

        assert r.status_code == 200
        body = r.json()
        assert body["job_id"] == "job-uuid-1"
        assert body["status"] == "pending"

    async def test_duplicate_job_returns_409(self, admin_client):
        existing = MagicMock()
        existing.data = [{"id": "job-1", "status": "running"}]

        with patch("app.api.v1.endpoints.admin.router.execute_db_safe", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = existing
            r = await admin_client.post("/api/v1/admin/ingest", json={"source": "loopnet-seed"})

        assert r.status_code == 409

    async def test_insert_no_data_returns_500(self, admin_client):
        no_existing = MagicMock()
        no_existing.data = []
        no_data = MagicMock()
        no_data.data = []

        with patch("app.api.v1.endpoints.admin.router.execute_db_safe", new_callable=AsyncMock) as mock_exec:
            mock_exec.side_effect = [no_existing, no_data]
            with patch("app.api.v1.endpoints.admin.router.wake_processor", new_callable=AsyncMock):
                r = await admin_client.post("/api/v1/admin/ingest", json={"source": "loopnet-seed"})

        assert r.status_code == 500
