from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from app.client import BackendClient
from app.tools._common import error_text, run_backend


def register_outreach_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def generate_outreach_draft(property_id: str) -> dict:
        """Generate and save a broker outreach email DRAFT (WRITE — draft only).

        Does NOT send email. Requires MCP_USER_ACCESS_TOKEN.

        Args:
            property_id: Property UUID to draft outreach for.
        """
        client = BackendClient()
        return await run_backend(
            "generate_outreach_draft",
            lambda: client.generate_outreach_draft(property_id),
        )

    @mcp.tool()
    async def get_outreach_draft(
        draft_id: str | None = None,
        property_id: str | None = None,
    ) -> dict:
        """Read a saved outreach draft (read-only).

        Provide either draft_id or property_id (latest draft for that property).
        Requires MCP_USER_ACCESS_TOKEN. Never sends email.

        Args:
            draft_id: Outreach draft UUID.
            property_id: Property UUID — returns the latest draft for this user.
        """
        if draft_id:
            client = BackendClient()
            return await run_backend(
                "get_outreach_draft",
                lambda: client.get_outreach_draft(draft_id),
            )
        if property_id:
            client = BackendClient()
            return await run_backend(
                "get_outreach_draft",
                lambda: client.get_latest_outreach_draft(property_id),
            )
        return error_text("Provide draft_id or property_id.")
