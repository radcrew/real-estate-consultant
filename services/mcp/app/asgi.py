"""ASGI app for Streamable HTTP (local uvicorn + Vercel Python Functions)."""

from __future__ import annotations

from app.auth.http_middleware import CaptureApiKeyMiddleware
from app.server import create_server

# Host 0.0.0.0 avoids FastMCP auto-enabling localhost-only DNS rebinding rules
# (those would reject Vercel Host headers). Stateless + JSON mode is required on
# Functions; Starlette lifespan must run so the session manager task group starts.
_mcp = create_server(
    host="0.0.0.0",
    port=8000,
    stateless_http=True,
    json_response=True,
)
app = CaptureApiKeyMiddleware(_mcp.streamable_http_app())
