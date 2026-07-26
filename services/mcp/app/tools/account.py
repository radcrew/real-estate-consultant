from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from app.client import BackendClient
from app.tools._common import run_backend


def register_account_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def list_saved_listings() -> dict:
        """List property ids saved by the authenticated user (read-only).

        Requires MCP_USER_ACCESS_TOKEN. Returns `{ "property_ids": [...] }`.
        Use get_listing for each id when you need detail.
        """
        client = BackendClient()
        return await run_backend("list_saved_listings", client.list_saved_listings)
