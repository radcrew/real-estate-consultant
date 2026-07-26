"""Build and configure the FastMCP server instance."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from app.config import settings
from app.tools import (
    register_account_tools,
    register_agents_tools,
    register_fit_tools,
    register_listings_tools,
    register_ping_tools,
    register_search_tools,
)


def create_server() -> FastMCP:
    mcp = FastMCP(
        name=settings.app_name,
        instructions=(
            "Radestate commercial real-estate assistant tools. "
            "You act as the authenticated user (MCP_USER_ACCESS_TOKEN). "
            "Prefer search_properties → get_listing → explain_fit for research. "
            "update_search_criteria writes/replaces session criteria. "
            "Outreach and intake tools arrive in a later phase. "
            "All tools call the FastAPI backend — this process holds no domain logic."
        ),
    )
    register_ping_tools(mcp)
    register_search_tools(mcp)
    register_listings_tools(mcp)
    register_fit_tools(mcp)
    register_account_tools(mcp)
    register_agents_tools(mcp)
    return mcp
