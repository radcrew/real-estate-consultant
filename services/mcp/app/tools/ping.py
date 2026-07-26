from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from app.client import BackendClient
from app.tools._common import run_backend


def register_ping_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def ping_backend() -> dict:
        """Health-check the radestate FastAPI backend (GET /api/v1/ping).

        Use this to verify BACKEND_API_URL is reachable before calling other tools.
        No authentication is required for ping.
        """
        client = BackendClient()
        return await run_backend("ping_backend", client.ping)
