"""Tests for MCP API key repository helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from app.repositories.mcp_api_keys import (
    create_mcp_api_key,
    list_mcp_api_keys,
    resolve_mcp_api_key_user_id,
    revoke_mcp_api_key,
)
from tests.repositories.conftest import make_supabase_client, make_table_mock

_UID = UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")
_KID = UUID("b2c3d4e5-f6a7-8901-bcde-f12345678901")


@pytest.fixture(autouse=True)
def _pepper(monkeypatch):
    monkeypatch.setattr("app.repositories.mcp_api_keys.settings.mcp_api_key_pepper", "test-pepper")


class TestCreateMcpApiKey:
    async def test_returns_plaintext_and_strips_hash(self):
        row = {
            "id": str(_KID),
            "user_id": str(_UID),
            "name": "Cursor",
            "key_prefix": "rad_xxxxxx",
            "key_hash": "should-not-leak",
            "scopes": ["*"],
            "created_at": "2026-01-01T00:00:00+00:00",
        }
        client = make_supabase_client([row])
        raw, meta = await create_mcp_api_key(client, user_id=_UID, name="Cursor")
        assert raw.startswith("rad_")
        assert "key_hash" not in meta
        assert meta["name"] == "Cursor"
        client.table.assert_called_with("mcp_api_keys")


class TestListMcpApiKeys:
    async def test_returns_rows(self):
        client = make_supabase_client(
            [{"id": str(_KID), "user_id": str(_UID), "name": "a", "key_prefix": "rad_aaa", "scopes": ["*"]}],
        )
        rows = await list_mcp_api_keys(client, _UID)
        assert len(rows) == 1
        assert rows[0]["id"] == str(_KID)


class TestRevokeMcpApiKey:
    async def test_returns_none_when_empty(self):
        client = make_supabase_client([])
        assert await revoke_mcp_api_key(client, user_id=_UID, key_id=_KID) is None

    async def test_returns_updated_row(self):
        client = make_supabase_client(
            [{"id": str(_KID), "user_id": str(_UID), "revoked_at": "2026-01-02T00:00:00+00:00"}],
        )
        row = await revoke_mcp_api_key(client, user_id=_UID, key_id=_KID)
        assert row is not None
        assert row["revoked_at"] is not None


class TestResolveMcpApiKey:
    async def test_resolves_matching_hash(self):
        from app.domain.mcp_api_keys import generate_mcp_api_key, hash_mcp_api_key, mcp_api_key_prefix

        raw = generate_mcp_api_key()
        digest = hash_mcp_api_key(raw, pepper="test-pepper")
        client = make_supabase_client(
            [
                {
                    "id": str(_KID),
                    "user_id": str(_UID),
                    "key_prefix": mcp_api_key_prefix(raw),
                    "key_hash": digest,
                    "revoked_at": None,
                    "expires_at": None,
                },
            ],
        )
        assert await resolve_mcp_api_key_user_id(client, raw) == _UID

    async def test_rejects_wrong_secret(self):
        from app.domain.mcp_api_keys import generate_mcp_api_key, hash_mcp_api_key, mcp_api_key_prefix

        raw = generate_mcp_api_key()
        other = generate_mcp_api_key()
        client = make_supabase_client(
            [
                {
                    "user_id": str(_UID),
                    "key_prefix": mcp_api_key_prefix(raw),
                    "key_hash": hash_mcp_api_key(raw, pepper="test-pepper"),
                    "revoked_at": None,
                    "expires_at": None,
                },
            ],
        )
        assert await resolve_mcp_api_key_user_id(client, other) is None

    async def test_rejects_expired(self):
        from app.domain.mcp_api_keys import generate_mcp_api_key, hash_mcp_api_key, mcp_api_key_prefix

        raw = generate_mcp_api_key()
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        client = make_supabase_client(
            [
                {
                    "user_id": str(_UID),
                    "key_prefix": mcp_api_key_prefix(raw),
                    "key_hash": hash_mcp_api_key(raw, pepper="test-pepper"),
                    "revoked_at": None,
                    "expires_at": past,
                },
            ],
        )
        assert await resolve_mcp_api_key_user_id(client, raw) is None
