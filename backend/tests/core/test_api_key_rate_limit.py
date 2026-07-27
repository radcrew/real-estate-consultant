"""Unit tests for per-key MCP API rate limiter."""

from __future__ import annotations

from uuid import uuid4

from app.core.api_key_rate_limit import ApiKeyRateLimiter


class TestApiKeyRateLimiter:
    def test_allows_until_max_then_blocks(self):
        limiter = ApiKeyRateLimiter(max_calls=3, window_seconds=60.0)
        kid = uuid4()
        assert limiter.allow(kid)
        assert limiter.allow(kid)
        assert limiter.allow(kid)
        assert not limiter.allow(kid)

    def test_keys_are_independent(self):
        limiter = ApiKeyRateLimiter(max_calls=1, window_seconds=60.0)
        a, b = uuid4(), uuid4()
        assert limiter.allow(a)
        assert not limiter.allow(a)
        assert limiter.allow(b)
