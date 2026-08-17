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


class TestKeyEviction:
    """Pruning timestamps is not enough — the keys themselves have to go."""

    def test_expired_keys_are_dropped(self, monkeypatch):
        limiter = SlidingWindowRateLimiter(max_calls=1, window_seconds=60.0)
        clock = 1_000.0
        monkeypatch.setattr("app.core.rate_limit.time.monotonic", lambda: clock)

        for index in range(50):
            limiter.allow(f"addr-{index}")
        assert len(limiter._hits) == 50

        # A whole window later none of those addresses has any live hit.
        clock += 61.0
        limiter.allow("someone-else")
        assert len(limiter._hits) == 1

    def test_a_key_still_inside_its_window_survives(self):
        # Eviction must not hand a live caller a fresh budget.
        limiter = SlidingWindowRateLimiter(max_calls=1, window_seconds=60.0)
        assert limiter.allow("busy")
        limiter._sweep(limiter._next_sweep)
        assert not limiter.allow("busy")

    def test_a_flood_of_keys_triggers_a_sweep_before_the_interval(self, monkeypatch):
        # The interval alone lets a caller minting keys grow the map unchecked; the
        # threshold is what bounds it, and client_ip trusts a caller-supplied header.
        monkeypatch.setattr("app.core.rate_limit.SWEEP_THRESHOLD_KEYS", 10)
        limiter = SlidingWindowRateLimiter(max_calls=1, window_seconds=60.0)
        clock = 1_000.0
        monkeypatch.setattr("app.core.rate_limit.time.monotonic", lambda: clock)

        for index in range(10):
            limiter.allow(f"addr-{index}")
        clock += 61.0
        for index in range(10, 20):
            limiter.allow(f"addr-{index}")

        # Without the threshold check every one of the 20 would still be resident.
        assert len(limiter._hits) < 20
