"""In-process sliding-window rate limit for MCP API keys."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock
from uuid import UUID


class ApiKeyRateLimiter:
    """Simple per-key limiter (single process / local server)."""

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
