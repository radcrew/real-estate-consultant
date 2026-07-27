"""MCP process entry — stdio by default; streamable-http for remote hosts."""

from __future__ import annotations

import logging
import sys

from app.config import settings
from app.logging import configure_logging
from app.server import create_server
from app.transport import run_transport

logger = logging.getLogger(__name__)


def main() -> None:
    configure_logging(settings.log_level)
    try:
        mcp = create_server()
        run_transport(mcp, settings)
    except ValueError as exc:
        logger.error("%s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
