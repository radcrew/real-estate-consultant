"""Stderr-only logging — stdout is reserved for MCP JSON-RPC when using stdio.

Cursor's MCP output panel tags *any* stderr line as ``[error]``, even INFO
records. Keep the MCP SDK / transport loggers at WARNING+ so routine
ping/ListTools traffic does not look like failures.
"""

from __future__ import annotations

import logging
import sys

from app.middleware.sanitize import redact_secrets

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


class _SecretRedactFilter(logging.Filter):
    """Never emit plaintext MCP API keys / JWTs in log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_secrets(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: redact_secrets(v) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    redact_secrets(a) if isinstance(a, str) else a for a in record.args
                )
        return True


def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"),
    )
    handler.addFilter(_SecretRedactFilter())
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    quiet_level = logging.WARNING
    for name in _QUIET_LOGGERS:
        logging.getLogger(name).setLevel(quiet_level)
