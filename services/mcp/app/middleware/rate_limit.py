"""In-process sliding-window rate limit for MCP tool calls."""

from __future__ import annotations

import threading
import time
from collections import deque


class RateLimitError(Exception):
    def __init__(self, message: str = "Rate limit exceeded. Wait a moment and retry.") -> None:
        super().__init__(message)


class SlidingWindowRateLimiter:
    """Simple process-local limiter (enough for stdio / single-node HTTP)."""

    def __init__(self, *, max_calls: int, window_seconds: float = 60.0) -> None:
        self._max_calls = max_calls
        self._window = window_seconds
        self._times: deque[float] = deque()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        now = time.monotonic()
        with self._lock:
            cutoff = now - self._window
            while self._times and self._times[0] < cutoff:
                self._times.popleft()
            if len(self._times) >= self._max_calls:
                raise RateLimitError(
                    f"Rate limit exceeded ({self._max_calls} calls / "
                    f"{int(self._window)}s). Wait and retry.",
                )
            self._times.append(now)
