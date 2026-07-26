from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from app.client import BackendClient
from app.tools._common import compact_search_response, run_backend


def register_search_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def search_properties(
        session_profile_id: str,
        limit: int = 10,
        offset: int = 0,
    ) -> dict:
        """Search properties for an existing search session (read-only).

        Requires MCP_USER_ACCESS_TOKEN. Returns compact match rows (id, location,
        price/size, match_score). Use get_listing for full property detail.

        Args:
            session_profile_id: Search profile UUID from intake complete / quick search.
            limit: Page size (1–100). Defaults to 10 to keep MCP context small.
            offset: Pagination offset.
        """
        capped = max(1, min(limit, 100))
        client = BackendClient()

        async def _call() -> dict[str, Any]:
            return await client.search_properties(
                session_profile_id,
                limit=capped,
                offset=max(0, offset),
            )

        return await run_backend(
            "search_properties",
            _call,
            transform=compact_search_response,
        )

    @mcp.tool()
    async def update_search_criteria(
        session_profile_id: str,
        criteria: dict[str, Any],
    ) -> dict:
        """Replace search criteria on the session's linked intake (WRITE).

        Overwrites prior criteria. Requires MCP_USER_ACCESS_TOKEN. Prefer asking
        the user before calling when criteria changes are consequential.

        Args:
            session_profile_id: Search profile UUID.
            criteria: Full criteria object to store (not a partial patch).
        """
        client = BackendClient()

        async def _call() -> dict[str, Any]:
            return await client.update_search_criteria(session_profile_id, criteria)

        return await run_backend("update_search_criteria", _call)
