"""Transport helpers — keep tool registry independent of how hosts connect."""

from __future__ import annotations

import logging
from typing import Literal

from mcp.server.fastmcp import FastMCP

from app.config import Settings

logger = logging.getLogger(__name__)

TransportName = Literal["stdio", "streamable-http"]


def apply_http_bind_settings(mcp: FastMCP, settings: Settings) -> None:
    mcp.settings.host = settings.mcp_http_host
    mcp.settings.port = settings.mcp_http_port


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
        mcp.run(transport="streamable-http")
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
