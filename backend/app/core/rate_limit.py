"""In-process sliding-window rate limiting (single process)."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock
from uuid import UUID


class SlidingWindowRateLimiter:
    """Simple per-key limiter (single process / local server).

    State is per process, so on a serverless host the effective ceiling is this limit
    times the number of live instances. That is accepted deliberately: a shared limiter
    needs Redis, and the cost of being approximate here is a caller occasionally getting
    a little more than their share — not an unbounded one.
    """

    def __init__(self, *, max_calls: int, window_seconds: float) -> None:
        self._max_calls = max_calls
        self._window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key_id: UUID | str) -> bool:
        now = time.monotonic()
        kid = str(key_id)
        with self._lock:
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
