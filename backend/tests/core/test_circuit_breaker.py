"""Tests for the in-process circuit breaker."""
from __future__ import annotations

from app.core.circuit_breaker import CircuitBreaker


class _Clock:
    """Hand-cranked time, so cooldown behaviour is asserted rather than slept through."""

    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def _breaker(threshold: int = 3, reset: float = 30.0):
    clock = _Clock()
    return CircuitBreaker(
        failure_threshold=threshold,
        reset_after_seconds=reset,
        time_source=clock,
    ), clock


class TestCircuitBreaker:
    def test_starts_closed(self):
        breaker, _ = _breaker()
        assert breaker.allow()
        assert not breaker.is_open

    def test_stays_closed_below_the_threshold(self):
        breaker, _ = _breaker(threshold=3)
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.allow()

    def test_opens_on_the_threshold_failure(self):
        breaker, _ = _breaker(threshold=3)
        for _ in range(3):
            breaker.record_failure()
        assert breaker.is_open
        assert not breaker.allow()

    def test_success_resets_the_count(self):
        """Only *consecutive* failures matter; an intermittent one is not an outage."""
        breaker, _ = _breaker(threshold=3)
        breaker.record_failure()
        breaker.record_failure()
        breaker.record_success()
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.allow()

    def test_refuses_calls_during_the_cooldown(self):
        breaker, clock = _breaker(threshold=1, reset=30.0)
        breaker.record_failure()
        clock.advance(29.0)
        assert not breaker.allow()

    def test_admits_one_probe_after_the_cooldown(self):
        breaker, clock = _breaker(threshold=1, reset=30.0)
        breaker.record_failure()
        clock.advance(31.0)
        assert breaker.allow()
        # The probe is in flight; nothing else gets through behind it.
        assert not breaker.allow()

    def test_successful_probe_closes_the_breaker(self):
        breaker, clock = _breaker(threshold=1, reset=30.0)
        breaker.record_failure()
        clock.advance(31.0)
        breaker.allow()
        breaker.record_success()
        assert not breaker.is_open
        assert breaker.allow()
        assert breaker.allow()

    def test_failed_probe_costs_another_full_window(self):
        breaker, clock = _breaker(threshold=1, reset=30.0)
        breaker.record_failure()
        clock.advance(31.0)
        breaker.allow()
        breaker.record_failure()
        clock.advance(29.0)
        assert not breaker.allow()
        clock.advance(2.0)
        assert breaker.allow()

    def test_threshold_below_one_is_clamped(self):
        """A zero threshold would open the breaker before anything had failed."""
        breaker = CircuitBreaker(failure_threshold=0, reset_after_seconds=1.0)
        assert breaker.allow()
        breaker.record_failure()
        assert breaker.is_open

    def test_failure_count_is_observable(self):
        breaker, _ = _breaker(threshold=3)
        breaker.record_failure()
        assert breaker.failure_count == 1
        breaker.record_success()
        assert breaker.failure_count == 0
