import pytest

from app.middleware.rate_limit import SlidingWindowRateLimiter
from app.tools import _common


@pytest.fixture(autouse=True)
def _relax_rate_limit() -> None:
    """Avoid flaky suite failures from the process-local rate limiter."""
    _common._rate_limiter = SlidingWindowRateLimiter(max_calls=10_000, window_seconds=60.0)
