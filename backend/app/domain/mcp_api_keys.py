"""Generate and hash MCP API keys (``rad_`` prefix)."""

from __future__ import annotations

import hashlib
import hmac
import secrets

MCP_API_KEY_PREFIX = "rad_"
# Indexed lookup prefix: "rad_" + first 8 chars of the secret body.
MCP_API_KEY_PREFIX_LEN = 12


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
