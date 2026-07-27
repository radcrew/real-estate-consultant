"""MCP edge auth — API key preferred; legacy JWT fallback for stdio."""

from __future__ import annotations

from app.auth.context import (
    clear_request_credential,
    get_backend_credential,
    get_request_credential,
    set_request_credential,
)
from app.auth.errors import AuthInvalidError, AuthRequiredError
from app.auth.providers import AuthContext, looks_like_mcp_api_key, resolve_env_credential

__all__ = [
    "AuthContext",
    "AuthInvalidError",
    "AuthRequiredError",
    "clear_request_credential",
    "get_backend_credential",
    "get_request_credential",
    "looks_like_mcp_api_key",
    "resolve_env_credential",
    "set_request_credential",
]
