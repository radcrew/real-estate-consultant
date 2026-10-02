"""Tests for admin endpoints."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

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
        with (
            patch(
                "app.api.v1.endpoints.admin.router.get_active_job_by_idempotency_key",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch(
                "app.api.v1.endpoints.admin.router.insert_job_row",
                new_callable=AsyncMock,
                return_value=_JOB_ROW,
            ),
            patch("app.api.v1.endpoints.admin.router.wake_processor", new_callable=AsyncMock),
        ):
            r = await admin_client.post("/api/v1/admin/ingest", json={"source": "loopnet-seed"})

        assert r.status_code == 200
        body = r.json()
        assert body["job_id"] == "job-uuid-1"
        assert body["status"] == "pending"

    async def test_duplicate_job_returns_409(self, admin_client):
        with patch(
            "app.api.v1.endpoints.admin.router.get_active_job_by_idempotency_key",
            new_callable=AsyncMock,
            return_value={"id": "job-1", "status": "running"},
        ):
            r = await admin_client.post("/api/v1/admin/ingest", json={"source": "loopnet-seed"})

        assert r.status_code == 409

    async def test_insert_no_data_returns_502(self, admin_client):
        with (
            patch(
                "app.api.v1.endpoints.admin.router.get_active_job_by_idempotency_key",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch(
                "app.api.v1.endpoints.admin.router.insert_job_row",
                new_callable=AsyncMock,
                side_effect=HTTPException(status_code=502, detail="Job insert returned no data."),
            ),
            patch("app.api.v1.endpoints.admin.router.wake_processor", new_callable=AsyncMock),
        ):
            r = await admin_client.post("/api/v1/admin/ingest", json={"source": "loopnet-seed"})

        assert r.status_code == 502


class TestGetJob:
    _ID = "6f1c2a9e-0000-4000-8000-0000000000aa"

    async def test_returns_the_job(self, admin_client):
        row = {
            "id": self._ID,
            "source": "loopnet-seed",
            "status": "done",
            "attempts": 1,
            "result": {"fetched": 10, "normalized": 9, "rejected": 1},
            "error": None,
        }
        with patch(
            "app.api.v1.endpoints.admin.router.get_job_row",
            new_callable=AsyncMock,
            return_value=row,
        ) as get_row:
            r = await admin_client.get(f"/api/v1/admin/jobs/{self._ID}")

        assert r.status_code == 200
        assert r.json() == row
        assert str(get_row.call_args.args[1]) == self._ID

    async def test_unknown_job_returns_404(self, admin_client):
        with patch(
            "app.api.v1.endpoints.admin.router.get_job_row",
            new_callable=AsyncMock,
            return_value=None,
        ):
            r = await admin_client.get(f"/api/v1/admin/jobs/{self._ID}")
        assert r.status_code == 404

    async def test_malformed_id_returns_422(self, admin_client):
        r = await admin_client.get("/api/v1/admin/jobs/not-a-uuid")
        assert r.status_code == 422
