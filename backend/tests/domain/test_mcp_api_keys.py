"""Unit tests for MCP API key generate / hash helpers."""

from __future__ import annotations

from app.domain.mcp_api_keys import (
    MCP_API_KEY_PREFIX,
    generate_mcp_api_key,
    hash_mcp_api_key,
    looks_like_mcp_api_key,
    mcp_api_key_prefix,
    verify_mcp_api_key,
)


class TestMcpApiKeyCrypto:
    def test_generate_has_prefix_and_entropy(self):
        key = generate_mcp_api_key()
        assert key.startswith(MCP_API_KEY_PREFIX)
        assert looks_like_mcp_api_key(key)
        assert len(key) > 20

    def test_hash_roundtrip(self):
        key = generate_mcp_api_key()
        digest = hash_mcp_api_key(key, pepper="test-pepper")
        assert verify_mcp_api_key(key, digest, pepper="test-pepper")
        assert not verify_mcp_api_key(key, digest, pepper="other")
        assert not verify_mcp_api_key(key + "x", digest, pepper="test-pepper")

    def test_prefix_length(self):
        key = "rad_abcdefghijklmnop"
        assert mcp_api_key_prefix(key) == "rad_abcdefgh"
        assert len(mcp_api_key_prefix(key)) == 12

    def test_looks_like_rejects_jwt_shaped(self):
        assert not looks_like_mcp_api_key("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abc.def")
        assert not looks_like_mcp_api_key("rad_short")
