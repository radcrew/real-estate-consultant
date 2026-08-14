"""In-process circuit breaker for a self-hosted dependency (single process)."""

from __future__ import annotations

import time
from collections.abc import Callable
from threading import Lock


class CircuitBreaker:
    """Stop calling a dependency that is failing, and probe it occasionally.

    State is per process — on Vercel, per instance — so each one learns independently
    that the dependency is down. That is less precise than a shared breaker backed by
    ElastiCache, and deliberately so: the trade buys a standing monthly cost, while the
    failure mode here is mild, a few extra failed calls before each instance trips.

    Only *infrastructure* failures belong in ``record_failure``. A dependency that
    answered and was merely wrong is up, and tripping on that would take a working
    service offline over bad content.
    """

    def __init__(
        self,
        *,
        failure_threshold: int,
        reset_after_seconds: float,
        time_source: Callable[[], float] = time.monotonic,
    ) -> None:
        self._threshold = max(1, failure_threshold)
        self._reset_after = reset_after_seconds
        self._now = time_source
        self._failures = 0
        self._opened_at: float | None = None
        self._lock = Lock()

    @property
    def is_open(self) -> bool:
        with self._lock:
            return self._opened_at is not None

    @property
    def failure_count(self) -> int:
        with self._lock:
            return self._failures

    def allow(self) -> bool:
        """Whether to attempt the call now.

        While open, exactly one probe is admitted per cooldown window: taking the clock
        forward as the probe leaves means a probe that fails costs another full window,
        and one that succeeds closes the breaker — no half-open state to track.
        """
        with self._lock:
            if self._opened_at is None:
                return True
            if self._now() - self._opened_at < self._reset_after:
                return False
            self._opened_at = self._now()
            return True

    def record_success(self) -> None:
        with self._lock:
            self._failures = 0
            self._opened_at = None

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1
            if self._failures >= self._threshold:
                self._opened_at = self._now()
