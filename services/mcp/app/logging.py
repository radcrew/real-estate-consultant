"""Stderr-only logging — stdout is reserved for MCP JSON-RPC when using stdio.

Cursor's MCP output panel tags *any* stderr line as ``[error]``, even INFO
records. Keep the MCP SDK / transport loggers at WARNING+ so routine
Ping/ListTools traffic does not look like failures.
"""

from __future__ import annotations

import logging
import sys

# Libraries that are chatty on stderr during normal stdio MCP operation.
_QUIET_LOGGERS = (
    "mcp",
    "mcp.server",
    "mcp.server.lowlevel",
    "mcp.server.lowlevel.server",
    "mcp.server.streamable_http",
    "uvicorn",
    "uvicorn.error",
    "uvicorn.access",
    "httpx",
    "httpcore",
    "asyncio",
)


def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"),
    )
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    quiet_level = logging.WARNING
    for name in _QUIET_LOGGERS:
        logging.getLogger(name).setLevel(quiet_level)
