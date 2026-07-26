from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from app.client import BackendClient
from app.tools._common import compact_featured_response, run_backend


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
    async def get_featured_listings() -> dict:
        """List daily featured listings (read-only, no auth required).

        Returns compact summaries; call get_listing for full detail.
        """
        client = BackendClient()
        return await run_backend(
            "get_featured_listings",
            client.get_featured_listings,
            transform=compact_featured_response,
        )
