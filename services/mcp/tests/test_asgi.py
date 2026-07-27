"""Smoke tests for Vercel / ASGI export."""

from __future__ import annotations


def test_asgi_app_exports_callable() -> None:
    from app.asgi import app

    assert callable(app)


def test_create_server_stateless_flag() -> None:
    from app.server import create_server

    mcp = create_server(host="0.0.0.0", stateless_http=True)
    assert mcp.settings.stateless_http is True
    assert mcp.settings.streamable_http_path == "/mcp"
