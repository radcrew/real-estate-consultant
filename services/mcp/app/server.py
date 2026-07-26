"""Build and configure the FastMCP server instance."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from app.config import settings
from app.tools import register_ping_tools


def create_server() -> FastMCP:
    mcp = FastMCP(
        name=settings.app_name,
        instructions=(
            "Radestate commercial real-estate assistant tools. "
            "Phase 0 exposes ping_backend only; search/intake/outreach arrive in later phases. "
            "All tools call the FastAPI backend — this process holds no domain logic."
        ),
    )
    register_ping_tools(mcp)
    return mcp
