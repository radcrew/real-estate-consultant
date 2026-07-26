"""MCP tool helpers — always return content dicts; never raise to the host."""

from __future__ import annotations

import json
from typing import Any


def ok_text(payload: Any) -> dict[str, Any]:
    text = payload if isinstance(payload, str) else json.dumps(payload, indent=2, default=str)
    return {"content": [{"type": "text", "text": text}]}


def error_text(message: str) -> dict[str, Any]:
    return {
        "isError": True,
        "content": [{"type": "text", "text": message}],
    }
