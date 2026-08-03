from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from app.client import BackendClient
from app.tools._common import compact_search_response, run_backend


def register_search_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def quick_search(
        location: str | None = None,
        property_types: list[str] | None = None,
        price_min: int | None = None,
        price_max: int | None = None,
        limit: int = 10,
    ) -> dict:
        """One-shot commercial property search (WRITE — creates a search session).

        Prefer this for ad-hoc location/budget/type queries. Creates a search
        profile via POST /api/v1/search/quick, then returns compact matches.
        Requires MCP_USER_ACCESS_TOKEN.

        Args:
            location: Free-text place, e.g. "Los Angeles, CA", "TX", "Austin, TX, US".
            property_types: Optional types such as ["Industrial"], ["Office"], ["Land"].
            price_min: Minimum asking price (USD integer).
            price_max: Maximum asking price (USD integer), e.g. 4000000 for under $4M.
            limit: Page size (1–100). Defaults to 10.
        """
        capped = max(1, min(limit, 100))
        client = BackendClient()

        async def _call() -> dict[str, Any]:
            created = await client.quick_search(
                location=location,
                property_types=property_types,
                price_min=price_min,
                price_max=price_max,
            )
            session_profile_id = str(created.get("search_profile_id") or "")
            if not session_profile_id:
                msg = "Backend quick search did not return search_profile_id"
                raise RuntimeError(msg)
            results = await client.search_properties(
                session_profile_id,
                limit=capped,
                offset=0,
            )
            compact = compact_search_response(results)
            compact["search_profile_id"] = session_profile_id
            return compact

        return await run_backend("quick_search", _call)

    @mcp.tool()
    async def search_properties(
        session_profile_id: str,
        limit: int = 10,
        offset: int = 0,
    ) -> dict:
        """Search properties for an existing search session (read-only).

        Requires MCP_USER_ACCESS_TOKEN. Returns compact match rows (id, location,
        price/size, match_score). Use get_listing for full property detail.
        For a new location/budget query, prefer quick_search instead.

        Args:
            session_profile_id: Search profile UUID returned by quick_search.
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
