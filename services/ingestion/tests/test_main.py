"""Tests for app.main — exception handlers."""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from fastapi import HTTPException
from fastapi.routing import APIRoute

from app.core.db_safe import SupabaseRequestError
from app.main import create_app


@pytest_asyncio.fixture
async def client():
    app = create_app()

    # Route that raises an HTTPException (4xx)
    @app.get("/test/http-error")
    async def _http_error():
        raise HTTPException(status_code=404, detail="not here")

    # Route that raises an HTTPException (5xx)
    @app.get("/test/http-500")
    async def _http_500():
        raise HTTPException(status_code=503, detail="unavailable")

    # Route that raises an unhandled exception
    @app.get("/test/unhandled")
    async def _unhandled():
        raise RuntimeError("kaboom")

    # Route that raises a Supabase request failure
    @app.get("/test/supabase-error")
    async def _supabase_error():
        raise SupabaseRequestError("could not reach Supabase")

    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as ac:
        yield ac


class TestHttpExceptionHandler:
    @pytest.mark.asyncio
    async def test_4xx_returns_correct_status(self, client):
        r = await client.get("/test/http-error")
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_4xx_returns_detail(self, client):
        r = await client.get("/test/http-error")
        assert r.json()["detail"] == "not here"

    @pytest.mark.asyncio
    async def test_5xx_returns_correct_status(self, client):
        r = await client.get("/test/http-500")
        assert r.status_code == 503


class TestSupabaseRequestErrorHandler:
    @pytest.mark.asyncio
    async def test_returns_502(self, client):
        r = await client.get("/test/supabase-error")
        assert r.status_code == 502

    @pytest.mark.asyncio
    async def test_returns_generic_message(self, client):
        r = await client.get("/test/supabase-error")
        assert "detail" in r.json()
        assert "database" in r.json()["detail"].lower()


class TestUnhandledExceptionHandler:
    @pytest.mark.asyncio
    async def test_returns_500(self, client):
        r = await client.get("/test/unhandled")
        assert r.status_code == 500

    @pytest.mark.asyncio
    async def test_returns_generic_message(self, client):
        r = await client.get("/test/unhandled")
        assert "detail" in r.json()
        assert "Internal server error" in r.json()["detail"]
