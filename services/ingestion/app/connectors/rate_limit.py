"""Outbound rate limiting for HTTP-fetching connectors.

Combines a per-source concurrency cap (``asyncio.Semaphore``) with a token-bucket
throttle so connectors fetch listing pages politely — required by the "lawful
ingestion" constraint and to keep the ingestion service from hammering a source
site (a reliability and ToS risk either way).

Future HTTP-based connectors should route their requests through
``RateLimitedFetcher.get()``; ``LoopNetSeedConnector`` reads a local dataset and
doesn't need this.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

import httpx


class TokenBucket:
    """Refills at ``rate`` tokens/second up to ``capacity``; ``acquire()`` waits for one."""

    def __init__(
        self,
        rate: float,
        capacity: float | None = None,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        if rate <= 0:
            raise ValueError("rate must be > 0")
        self._rate = rate
        self._capacity = capacity if capacity is not None else rate
        self._tokens = self._capacity
        self._clock = clock
        self._sleep = sleep
        self._updated = clock()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: float = 1.0) -> None:
        async with self._lock:
            while True:
                now = self._clock()
                refill = (now - self._updated) * self._rate
                self._tokens = min(self._capacity, self._tokens + refill)
                self._updated = now
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return
                await self._sleep((tokens - self._tokens) / self._rate)


class RateLimiter:
    """Caps in-flight requests at ``max_concurrency`` and paces new ones via a token bucket."""

    def __init__(
        self,
        max_concurrency: int,
        rate_per_second: float,
        *,
        burst: float | None = None,
    ) -> None:
        if max_concurrency <= 0:
            raise ValueError("max_concurrency must be > 0")
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._bucket = TokenBucket(rate_per_second, burst)

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[None]:
        await self._bucket.acquire()
        async with self._semaphore:
            yield


class RateLimitedFetcher:
    """Thin ``httpx.AsyncClient`` wrapper that runs every request through a ``RateLimiter``."""

    def __init__(self, client: httpx.AsyncClient, limiter: RateLimiter) -> None:
        self._client = client
        self._limiter = limiter

    async def get(self, url: str, **kwargs: object) -> httpx.Response:
        async with self._limiter.acquire():
            return await self._client.get(url, **kwargs)
