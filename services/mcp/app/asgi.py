"""ASGI app for Streamable HTTP (local uvicorn + Vercel Python Functions)."""

from __future__ import annotations

from app.auth.http_middleware import CaptureApiKeyMiddleware
from app.server import create_server

# Host 0.0.0.0 avoids FastMCP auto-enabling localhost-only DNS rebinding rules
# (those would reject Vercel Host headers). Stateless mode is required on Functions.
_mcp = create_server(host="0.0.0.0", port=8000, stateless_http=True)
app = CaptureApiKeyMiddleware(_mcp.streamable_http_app())
