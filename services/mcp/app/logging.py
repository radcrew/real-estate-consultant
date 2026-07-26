"""Stderr-only logging — stdout is reserved for MCP JSON-RPC when using stdio."""

from __future__ import annotations

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"),
    )
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
