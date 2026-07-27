"""Transport helpers — keep tool registry independent of how hosts connect."""

from __future__ import annotations

import logging
from typing import Literal

from mcp.server.fastmcp import FastMCP

from app.auth.http_middleware import CaptureApiKeyMiddleware
from app.config import Settings

logger = logging.getLogger(__name__)

TransportName = Literal["stdio", "streamable-http"]


def apply_http_bind_settings(mcp: FastMCP, settings: Settings) -> None:
    mcp.settings.host = settings.mcp_http_host
    mcp.settings.port = settings.mcp_http_port


async def _run_streamable_http(mcp: FastMCP) -> None:
    """Run Streamable HTTP with API-key capture middleware."""
    import uvicorn

    # Prefer shared ASGI factory when already configured for HTTP (stateless optional).
    from app.auth.http_middleware import CaptureApiKeyMiddleware

    app = CaptureApiKeyMiddleware(mcp.streamable_http_app())

    config = uvicorn.Config(
        app,
        host=mcp.settings.host,
        port=mcp.settings.port,
        log_level=mcp.settings.log_level.lower(),
    )
    server = uvicorn.Server(config)
    await server.serve()


def run_transport(mcp: FastMCP, settings: Settings) -> None:
    transport = settings.mcp_transport.strip().lower().replace("_", "-")
    if transport in {"streamable-http", "streamablehttp", "http"}:
        apply_http_bind_settings(mcp, settings)
        logger.info(
            "starting radestate MCP server transport=streamable-http host=%s port=%s path=%s",
            settings.mcp_http_host,
            settings.mcp_http_port,
            mcp.settings.streamable_http_path,
        )
        import anyio

        anyio.run(_run_streamable_http, mcp)
        return

    if transport != "stdio":
        msg = (
            f"Unsupported MCP_TRANSPORT={settings.mcp_transport!r} "
            "(use stdio or streamable-http)"
        )
        raise ValueError(msg)

    logger.info(
        "starting radestate MCP server transport=stdio backend=%s",
        settings.backend_api_url,
    )
    mcp.run(transport="stdio")
