"""Tests for /health and /api/v1/ping endpoints (no DB deps)."""
from unittest.mock import patch

import pytest


class TestHealth:
    async def test_health_returns_ok(self, client):
        r = await client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}

    async def test_health_live_returns_ok(self, client):
        r = await client.get("/health/live")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}

    async def test_health_ready_all_ok(self, client):
        with (
            patch("app.api.system.check_db", return_value=True),
            patch("app.api.system.check_supabase", return_value=True),
        ):
            r = await client.get("/health/ready")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert body["checks"]["db"] == "ok"
        assert body["checks"]["supabase"] == "ok"

    async def test_health_ready_db_down_returns_503(self, client):
        with (
            patch("app.api.system.check_db", return_value=False),
            patch("app.api.system.check_supabase", return_value=True),
        ):
            r = await client.get("/health/ready")
        assert r.status_code == 503
        assert r.json()["status"] == "degraded"
        assert r.json()["checks"]["db"] == "fail"

    async def test_health_ready_supabase_down_returns_503(self, client):
        with (
            patch("app.api.system.check_db", return_value=True),
            patch("app.api.system.check_supabase", return_value=False),
        ):
            r = await client.get("/health/ready")
        assert r.status_code == 503
        assert r.json()["checks"]["supabase"] == "fail"


class TestPing:
    async def test_ping_returns_pong(self, client):
        r = await client.get("/api/v1/ping")
        assert r.status_code == 200
        assert r.json() == {"message": "pong"}
