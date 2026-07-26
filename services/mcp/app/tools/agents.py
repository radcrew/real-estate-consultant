from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from app.client import BackendClient
from app.tools._common import compact_agent_response, run_backend


def register_agents_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_agent(broker: str) -> dict:
        """Get a broker/agent profile and their listings (read-only).

        Requires MCP_USER_ACCESS_TOKEN (backend mounts agents under auth).

        Args:
            broker: Broker name as stored on listings (listing_broker_name).
        """
        client = BackendClient()
        return await run_backend(
            "get_agent",
            lambda: client.get_agent(broker),
            transform=compact_agent_response,
        )
