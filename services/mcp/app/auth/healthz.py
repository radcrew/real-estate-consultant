"""Liveness route for PaaS health checks (Render, etc.)."""

from __future__ import annotations

from starlette.types import ASGIApp, Receive, Scope, Send

_HEALTH_PATHS = frozenset({"/healthz", "/health"})
_BODY = b'{"status":"ok"}'
_HEADERS = [
    (b"content-type", b"application/json"),
    (b"content-length", str(len(_BODY)).encode("ascii")),
]


class HealthzMiddleware:
    """Answer GET /healthz (and /health) with 200 before the MCP app."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            scope["type"] == "http"
            and scope.get("method") == "GET"
            and scope.get("path") in _HEALTH_PATHS
        ):
            await send({"type": "http.response.start", "status": 200, "headers": _HEADERS})
            await send({"type": "http.response.body", "body": _BODY})
            return
        await self.app(scope, receive, send)
