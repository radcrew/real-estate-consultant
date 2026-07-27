"""Generate and hash MCP API keys (``rad_`` prefix)."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Iterable

MCP_API_KEY_PREFIX = "rad_"
# Indexed lookup prefix: "rad_" + first 8 chars of the secret body.
MCP_API_KEY_PREFIX_LEN = 12

ALLOWED_MCP_SCOPES: frozenset[str] = frozenset(
    {
        "*",
        "mcp:read",
        "mcp:write",
        "mcp:admin",
    },
)


def looks_like_mcp_api_key(token: str) -> bool:
    return token.startswith(MCP_API_KEY_PREFIX) and len(token) > MCP_API_KEY_PREFIX_LEN


def generate_mcp_api_key() -> str:
    """Return a new plaintext key. Caller must hash before storage."""
    body = secrets.token_urlsafe(32)
    return f"{MCP_API_KEY_PREFIX}{body}"


def mcp_api_key_prefix(raw_key: str) -> str:
    return raw_key[:MCP_API_KEY_PREFIX_LEN]


def hash_mcp_api_key(raw_key: str, *, pepper: str) -> str:
    material = f"{pepper}{raw_key}".encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def verify_mcp_api_key(raw_key: str, key_hash: str, *, pepper: str) -> bool:
    expected = hash_mcp_api_key(raw_key, pepper=pepper)
    return hmac.compare_digest(expected, key_hash)


def normalize_mcp_scopes(scopes: Iterable[str] | None) -> list[str]:
    if not scopes:
        return ["*"]
    cleaned = [s.strip() for s in scopes if str(s).strip()]
    if not cleaned:
        return ["*"]
    unknown = [s for s in cleaned if s not in ALLOWED_MCP_SCOPES]
    if unknown:
        msg = f"Unsupported MCP API key scopes: {', '.join(unknown)}"
        raise ValueError(msg)
    if "*" in cleaned:
        return ["*"]
    return list(dict.fromkeys(cleaned))


def mcp_scopes_allow(scopes: Iterable[str] | None, required: str) -> bool:
    """Return True if scopes grant ``required`` (``*`` / ``mcp:admin`` grant all)."""
    have = set(scopes or [])
    if "*" in have or "mcp:admin" in have:
        return True
    if required in have:
        return True
    if required == "mcp:read" and "mcp:write" in have:
        return True
    return False
