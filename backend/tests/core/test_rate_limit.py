"""Unit tests for the in-process sliding-window rate limiter."""

from __future__ import annotations

from uuid import uuid4

from app.core.rate_limit import ApiKeyRateLimiter, SlidingWindowRateLimiter


class TestSlidingWindowRateLimiter:
    def test_allows_until_max_then_blocks(self):
        limiter = SlidingWindowRateLimiter(max_calls=3, window_seconds=60.0)
        kid = uuid4()
        assert limiter.allow(kid)
        assert limiter.allow(kid)
        assert limiter.allow(kid)
        assert not limiter.allow(kid)

    def test_keys_are_independent(self):
        limiter = SlidingWindowRateLimiter(max_calls=1, window_seconds=60.0)
        a, b = uuid4(), uuid4()
        assert limiter.allow(a)
        assert not limiter.allow(a)
        assert limiter.allow(b)

    def test_uuid_and_string_keys_are_the_same_bucket(self):
        """Callers pass whichever they hold; they must not get two budgets for one key."""
        limiter = SlidingWindowRateLimiter(max_calls=1, window_seconds=60.0)
        kid = uuid4()
        assert limiter.allow(kid)
        assert not limiter.allow(str(kid))

    def test_api_key_alias_still_resolves(self):
        """The MCP limiter kept its old name through the rename."""
        assert ApiKeyRateLimiter is SlidingWindowRateLimiter
