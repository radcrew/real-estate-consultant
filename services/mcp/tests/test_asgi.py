"""Smoke tests for Vercel / ASGI export."""

from __future__ import annotations

from starlette.testclient import TestClient

from app.asgi import create_asgi_app


def test_asgi_app_exports_callable() -> None:
    assert callable(create_asgi_app())


def test_create_server_stateless_flag() -> None:
    from app.server import create_server

    mcp = create_server(host="0.0.0.0", stateless_http=True)
    assert mcp.settings.stateless_http is True
    assert mcp.settings.json_response is True
    assert mcp.settings.streamable_http_path == "/mcp"


def test_mcp_initialize_over_asgi() -> None:
    """Lifespan must start the StreamableHTTP session manager (Vercel runs lifespan)."""
    with TestClient(create_asgi_app()) as client:
        response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "0.0.1"},
                },
            },
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
            },
        )
    assert response.status_code == 200
    assert "application/json" in (response.headers.get("content-type") or "")
    payload = response.json()
    assert payload["result"]["serverInfo"]["name"] == "radestate"
    assert "protocolVersion" in payload["result"]


def test_health_endpoint() -> None:
    with TestClient(create_asgi_app()) as client:
        response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "radestate"
    assert "backend_api_url" in body


def test_cors_preflight_mcp() -> None:
    with TestClient(create_asgi_app()) as client:
        response = client.options(
            "/mcp",
            headers={
                "Origin": "http://localhost:6274",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )
    assert response.status_code in {200, 204}
    assert response.headers.get("access-control-allow-origin") == "*"
