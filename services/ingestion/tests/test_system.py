"""Tests for system health endpoints."""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=create_app()), base_url="http://test") as ac:
        yield ac


class TestHealthLive:
    @pytest.mark.asyncio
    async def test_returns_200(self, client):
        r = await client.get("/health/live")
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_returns_ok_status(self, client):
        r = await client.get("/health/live")
        assert r.json()["status"] == "ok"

    @pytest.mark.asyncio
    async def test_head_returns_200(self, client):
        r = await client.head("/health/live")
        assert r.status_code == 200


class TestHealthReady:
    @pytest.mark.asyncio
    async def test_returns_200_when_supabase_ok(self, client):
        mock_resp = AsyncMock()
        mock_resp.status_code = 200

        mock_http = AsyncMock()
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_http.get = AsyncMock(return_value=mock_resp)

        with patch("app.api.system.httpx.AsyncClient", return_value=mock_http):
            r = await client.get("/health/ready")

        assert r.status_code == 200
        assert r.json()["status"] == "ok"
        assert r.json()["checks"]["supabase"] == "ok"

    @pytest.mark.asyncio
    async def test_returns_503_when_supabase_fails(self, client):
        mock_http = AsyncMock()
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_http.get = AsyncMock(side_effect=Exception("connection refused"))

        with patch("app.api.system.httpx.AsyncClient", return_value=mock_http):
            r = await client.get("/health/ready")

        assert r.status_code == 503
        assert r.json()["status"] == "degraded"
        assert r.json()["checks"]["supabase"] == "fail"

    @pytest.mark.asyncio
    async def test_returns_503_when_supabase_returns_500(self, client):
        mock_resp = AsyncMock()
        mock_resp.status_code = 500

        mock_http = AsyncMock()
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_http.get = AsyncMock(return_value=mock_resp)

        with patch("app.api.system.httpx.AsyncClient", return_value=mock_http):
            r = await client.get("/health/ready")

        assert r.status_code == 503

    @pytest.mark.asyncio
    async def test_response_includes_version_and_started_at(self, client):
        mock_resp = AsyncMock()
        mock_resp.status_code = 200

        mock_http = AsyncMock()
        mock_http.__aenter__ = AsyncMock(return_value=mock_http)
        mock_http.__aexit__ = AsyncMock(return_value=False)
        mock_http.get = AsyncMock(return_value=mock_resp)

        with patch("app.api.system.httpx.AsyncClient", return_value=mock_http):
            r = await client.get("/health/ready")

        body = r.json()
        assert "version" in body
        assert "started_at" in body
