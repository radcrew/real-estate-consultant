from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from app.client import BackendClient
from app.tools._common import compact_similar_response, run_backend


def register_listings_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_listing(property_id: str) -> dict:
        """Fetch full listing detail by property id (read-only, no auth required).

        Args:
            property_id: Property UUID.
        """
        client = BackendClient()
        return await run_backend(
            "get_listing",
            lambda: client.get_listing(property_id),
        )

    @mcp.tool()
    async def get_similar_listings(property_id: str, limit: int = 6) -> dict:
        """Find listings similar to a seed property via embedding similarity (read-only).

        Requires backend embeddings keys (HF_TOKEN preferred). Returns compact
        summaries with match_score (0–100); call get_listing for full detail.

        Args:
            property_id: Seed property UUID.
            limit: Max results (1–20, default 6).
        """
        capped = max(1, min(int(limit), 20))
        client = BackendClient()
        return await run_backend(
            "get_similar_listings",
            lambda: client.get_similar_listings(property_id, limit=capped),
            transform=compact_similar_response,
        )
