from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from app.client import BackendClient
from app.tools._common import run_backend


def register_admin_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def enqueue_ingest(source: str = "loopnet-seed") -> dict:
        """Enqueue an ingestion job (WRITE — admin only).

        Requires MCP_USER_ACCESS_TOKEN for a user with profiles.is_admin.
        Backend rejects non-admins with 403.

        Args:
            source: Connector/source name (default loopnet-seed).
        """
        client = BackendClient()
        return await run_backend(
            "enqueue_ingest",
            lambda: client.enqueue_ingest(source),
        )

    @mcp.tool()
    async def list_listing_submissions() -> dict:
        """List user listing submissions for admin review (read-only, admin only).

        Requires an admin MCP_USER_ACCESS_TOKEN. Backend rejects non-admins with 403.
        """
        client = BackendClient()

        async def _call() -> dict[str, Any]:
            rows = await client.list_listing_submissions()
            return {"submissions": rows, "count": len(rows)}

        return await run_backend("list_listing_submissions", _call)
