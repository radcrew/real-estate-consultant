"""ASGI healthz middleware tests."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth.healthz import HealthzMiddleware
from app.server import create_server
from app.transport import build_http_app


@pytest.mark.asyncio
async def test_healthz_returns_ok() -> None:
    async def _inner(scope, receive, send):  # noqa: ANN001
        raise AssertionError("inner app should not run for /healthz")

    app = HealthzMiddleware(_inner)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_build_http_app_exposes_healthz() -> None:
    app = build_http_app(create_server())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
