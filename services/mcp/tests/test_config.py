"""Settings / env binding for MCP (incl. Render PORT)."""

from __future__ import annotations

from app.config import Settings


def test_mcp_http_port_defaults_to_8900(monkeypatch) -> None:
    monkeypatch.delenv("MCP_HTTP_PORT", raising=False)
    monkeypatch.delenv("PORT", raising=False)
    settings = Settings(_env_file=None)
    assert settings.mcp_http_port == 8900


def test_mcp_http_port_from_port_env(monkeypatch) -> None:
    monkeypatch.delenv("MCP_HTTP_PORT", raising=False)
    monkeypatch.setenv("PORT", "10000")
    settings = Settings(_env_file=None)
    assert settings.mcp_http_port == 10000


def test_mcp_http_port_prefers_explicit_over_port(monkeypatch) -> None:
    monkeypatch.setenv("PORT", "10000")
    monkeypatch.setenv("MCP_HTTP_PORT", "8901")
    settings = Settings(_env_file=None)
    assert settings.mcp_http_port == 8901
