"""Request-scoped and process credential context."""

from __future__ import annotations

from contextvars import ContextVar, Token

from app.auth.errors import AuthRequiredError
from app.auth.providers import resolve_env_credential
from app.config import settings

_request_credential: ContextVar[str | None] = ContextVar("mcp_request_credential", default=None)


def get_request_credential() -> str | None:
    value = _request_credential.get()
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def set_request_credential(credential: str | None) -> Token:
    return _request_credential.set(credential)


def clear_request_credential(token: Token) -> None:
    _request_credential.reset(token)


def _http_transport() -> bool:
    transport = settings.mcp_transport.strip().lower().replace("_", "-")
    return transport in {"streamable-http", "streamablehttp", "http"}


def get_backend_credential() -> str:
    """Return the Bearer credential for backend calls.

    - Streamable HTTP: **request header only** (no shared process-env fallback).
    - Stdio: ``MCP_API_KEY`` then legacy ``MCP_USER_ACCESS_TOKEN``.
    """
    header = get_request_credential()
    if header:
        return header

    if _http_transport():
        raise AuthRequiredError(
            "HTTP MCP requests require Authorization: Bearer <rad_…> or X-API-Key. "
            "Process env credentials are not used for Streamable HTTP tool calls.",
        )

    env = resolve_env_credential()
    if env:
        return env.credential

    raise AuthRequiredError()
