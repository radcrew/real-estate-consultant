"""ASGI app for Streamable HTTP (local uvicorn + Vercel Python Functions)."""

from __future__ import annotations

from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.auth.http_middleware import CaptureApiKeyMiddleware
from app.config import settings
from app.server import create_server


def create_asgi_app() -> ASGIApp:
    """Build a fresh ASGI app (stateless MCP + health + CORS).

    A factory is required because FastMCP's StreamableHTTP session manager
    lifespan can only be entered once per instance.
    """
    # Host 0.0.0.0 avoids FastMCP auto-enabling localhost-only DNS rebinding rules
    # (those would reject Vercel Host headers). Stateless + JSON mode is required on
    # Functions; Starlette lifespan must run so the session manager task group starts.
    mcp = create_server(
        host="0.0.0.0",
        port=8000,
        stateless_http=True,
        json_response=True,
    )

    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(_request: Request) -> Response:
        return JSONResponse(
            {
                "status": "ok",
                "service": settings.app_name,
                "backend_api_url": settings.backend_api_url,
            }
        )

    # CORS for MCP Inspector / browser hosts. Tool auth still requires API key headers.
    inner = CaptureApiKeyMiddleware(mcp.streamable_http_app())
    return CORSMiddleware(
        inner,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["Mcp-Session-Id", "mcp-session-id"],
    )


app = create_asgi_app()
