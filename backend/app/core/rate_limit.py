"""In-process sliding-window rate limiting (single process)."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock
from uuid import UUID


# Sweep as soon as the map passes this, rather than waiting for the interval. Callers are
# keyed partly by a header the client controls (see ``client_ip``), so a flood of unique
# keys must not be able to outrun the cleanup between sweeps.
SWEEP_THRESHOLD_KEYS = 10_000


class SlidingWindowRateLimiter:
    """Simple per-key limiter (single process / local server).

    State is per process, so on a serverless host the effective ceiling is this limit
    times the number of live instances. That is accepted deliberately: a shared limiter
    needs Redis, and the cost of being approximate here is a caller occasionally getting
    a little more than their share — not an unbounded one.

    Keys are evicted once their whole window has passed. Pruning timestamps alone is not
    enough: the key stays behind holding an empty deque, so every address ever seen
    accumulates forever. That matters most under exactly the abuse this defends against,
    because ``client_ip`` reads a caller-supplied header — an attacker varying it per
    request mints unlimited keys, and the limiter becomes the memory leak.
    """

    def __init__(self, *, max_calls: int, window_seconds: float) -> None:
        self._max_calls = max_calls
        self._window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()
        self._next_sweep = 0.0

    def _sweep(self, now: float) -> None:
        """Drop keys whose newest hit has aged out. Caller holds the lock.

        A key with no hit inside the window would prune to an empty deque anyway, so
        removing it is indistinguishable from keeping it — the next call recreates it.
        """
        cutoff = now - self._window
        stale = [key for key, hits in self._hits.items() if not hits or hits[-1] < cutoff]
        for key in stale:
            del self._hits[key]
        self._next_sweep = now + self._window

    def allow(self, key_id: UUID | str) -> bool:
        now = time.monotonic()
        kid = str(key_id)
        with self._lock:
            if now >= self._next_sweep or len(self._hits) > SWEEP_THRESHOLD_KEYS:
                self._sweep(now)
            bucket = self._hits[kid]
            cutoff = now - self._window
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= self._max_calls:
                return False
            bucket.append(now)
            return True


# Historical name: this started as the MCP API-key limiter before intake needed one too.
ApiKeyRateLimiter = SlidingWindowRateLimiter
