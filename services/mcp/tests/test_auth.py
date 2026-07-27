"""Tests for MCP API-key / JWT credential resolution."""

from __future__ import annotations

import pytest

from app.auth.context import (
    clear_request_credential,
    get_backend_credential,
    set_request_credential,
)
from app.auth.errors import AuthRequiredError
from app.auth.providers import credential_from_headers, resolve_env_credential
from app.client.backend import BackendClient


def test_resolve_env_prefers_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    from app import config

    monkeypatch.setattr(config.settings, "mcp_api_key", "rad_abcdefghijklmnop")
    monkeypatch.setattr(config.settings, "mcp_user_access_token", "jwt-should-not-win")
    ctx = resolve_env_credential()
    assert ctx is not None
    assert ctx.source == "env_api_key"
    assert ctx.credential.startswith("rad_")


def test_resolve_env_falls_back_to_jwt(monkeypatch: pytest.MonkeyPatch) -> None:
    from app import config

    monkeypatch.setattr(config.settings, "mcp_api_key", "")
    monkeypatch.setattr(config.settings, "mcp_user_access_token", "legacy-jwt")
    ctx = resolve_env_credential()
    assert ctx is not None
    assert ctx.source == "env_jwt"


def test_stdio_credential_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    from app import config

    monkeypatch.setattr(config.settings, "mcp_transport", "stdio")
    monkeypatch.setattr(config.settings, "mcp_api_key", "rad_abcdefghijklmnop")
    monkeypatch.setattr(config.settings, "mcp_user_access_token", "")
    assert get_backend_credential() == "rad_abcdefghijklmnop"


def test_http_requires_header(monkeypatch: pytest.MonkeyPatch) -> None:
    from app import config

    monkeypatch.setattr(config.settings, "mcp_transport", "streamable-http")
    monkeypatch.setattr(config.settings, "mcp_api_key", "rad_abcdefghijklmnop")
    with pytest.raises(AuthRequiredError, match="HTTP MCP"):
        get_backend_credential()


def test_http_uses_request_header(monkeypatch: pytest.MonkeyPatch) -> None:
    from app import config

    monkeypatch.setattr(config.settings, "mcp_transport", "streamable-http")
    token = set_request_credential("rad_from_header_valuexx")
    try:
        assert get_backend_credential() == "rad_from_header_valuexx"
    finally:
        clear_request_credential(token)


def test_credential_from_headers_bearer_and_x_api_key() -> None:
    assert (
        credential_from_headers("Bearer rad_abcdefghijklmnop", None)
        == "rad_abcdefghijklmnop"
    )
    assert credential_from_headers(None, "rad_abcdefghijklmnop") == "rad_abcdefghijklmnop"


def test_backend_client_explicit_token() -> None:
    client = BackendClient(base_url="http://127.0.0.1:8888", access_token="explicit")
    assert client._headers(auth=True)["Authorization"] == "Bearer explicit"


def test_backend_client_missing_auth_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    from app import config

    monkeypatch.setattr(config.settings, "mcp_transport", "stdio")
    monkeypatch.setattr(config.settings, "mcp_api_key", "")
    monkeypatch.setattr(config.settings, "mcp_user_access_token", "")
    client = BackendClient(base_url="http://127.0.0.1:8888", access_token=None)
    with pytest.raises(AuthRequiredError):
        client.require_auth()
