from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from app.client import BackendClient
from app.tools._common import run_backend


def register_fit_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def explain_fit(session_profile_id: str, property_id: str) -> dict:
        """Explain why a property matches the session's search criteria (read-only).

        Calls the backend LLM fit endpoint. Does not persist. Requires
        MCP_USER_ACCESS_TOKEN and access to the search profile.

        Args:
            session_profile_id: Search profile UUID.
            property_id: Property UUID from search_properties or get_listing.
        """
        client = BackendClient()
        return await run_backend(
            "explain_fit",
            lambda: client.explain_fit(session_profile_id, property_id),
        )
