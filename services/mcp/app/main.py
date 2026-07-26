"""MCP process entry — stdio by default (stdout is the JSON-RPC wire)."""

from __future__ import annotations

import logging
import sys

from app.config import settings
from app.logging import configure_logging
from app.server import create_server

logger = logging.getLogger(__name__)


def main() -> None:
    configure_logging(settings.log_level)
    transport = settings.mcp_transport.strip().lower()
    if transport != "stdio":
        logger.error(
            "Unsupported MCP_TRANSPORT=%r (Phase 0 supports stdio only)",
            settings.mcp_transport,
        )
        sys.exit(1)

    logger.info(
        "starting radestate MCP server transport=stdio backend=%s",
        settings.backend_api_url,
    )
    mcp = create_server()
    # FastMCP.run defaults to stdio; do not log to stdout after this.
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
