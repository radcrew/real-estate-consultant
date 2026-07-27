"""Resolve MCP credentials from settings / headers."""

from __future__ import annotations

from dataclasses import dataclass

from app.config import settings

MCP_API_KEY_PREFIX = "rad_"


@dataclass(frozen=True, slots=True)
class AuthContext:
    credential: str
    source: str  # "header" | "env_api_key" | "env_jwt"


def looks_like_mcp_api_key(token: str) -> bool:
    return token.startswith(MCP_API_KEY_PREFIX) and len(token) > len(MCP_API_KEY_PREFIX) + 8


def resolve_env_credential() -> AuthContext | None:
    """Prefer ``MCP_API_KEY``; fall back to legacy ``MCP_USER_ACCESS_TOKEN``."""
    api_key = (settings.mcp_api_key or "").strip()
    if api_key:
        return AuthContext(credential=api_key, source="env_api_key")
    jwt = (settings.mcp_user_access_token or "").strip()
    if jwt:
        return AuthContext(credential=jwt, source="env_jwt")
    return None


def credential_from_headers(authorization: str | None, x_api_key: str | None) -> str | None:
    if x_api_key and x_api_key.strip():
        return x_api_key.strip()
    if authorization and authorization.strip():
        value = authorization.strip()
        if value.lower().startswith("bearer "):
            token = value[7:].strip()
            return token or None
        if looks_like_mcp_api_key(value):
            return value
    return None
