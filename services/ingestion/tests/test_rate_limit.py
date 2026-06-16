from __future__ import annotations

import asyncio

import httpx
import pytest

from app.connectors.rate_limit import RateLimitedFetcher, RateLimiter, TokenBucket


@pytest.mark.asyncio
async def test_token_bucket_allows_burst_up_to_capacity() -> None:
    bucket = TokenBucket(rate=1.0, capacity=3, clock=lambda: 0.0, sleep=asyncio.sleep)

    # All 3 starting tokens are available immediately, with no waiting.
    for _ in range(3):
        await bucket.acquire()


@pytest.mark.asyncio
async def test_token_bucket_waits_for_refill() -> None:
    clock = 0.0
    sleeps: list[float] = []

    def fake_clock() -> float:
        return clock

    async def fake_sleep(seconds: float) -> None:
        nonlocal clock
        sleeps.append(seconds)
        clock += seconds

    bucket = TokenBucket(rate=2.0, capacity=1, clock=fake_clock, sleep=fake_sleep)

    await bucket.acquire()  # consumes the single starting token
    await bucket.acquire()  # must wait for a refill at 2 tokens/second

    assert sleeps == [0.5]


@pytest.mark.asyncio
async def test_rate_limiter_caps_concurrency() -> None:
    limiter = RateLimiter(max_concurrency=2, rate_per_second=1000.0)
    in_flight = 0
    max_in_flight = 0

    async def worker() -> None:
        nonlocal in_flight, max_in_flight
        async with limiter.acquire():
            in_flight += 1
            max_in_flight = max(max_in_flight, in_flight)
            await asyncio.sleep(0.01)
            in_flight -= 1

    await asyncio.gather(*(worker() for _ in range(5)))

    assert max_in_flight <= 2


@pytest.mark.asyncio
async def test_rate_limited_fetcher_get() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="https://example.test") as client:
        limiter = RateLimiter(max_concurrency=1, rate_per_second=1000.0)
        fetcher = RateLimitedFetcher(client, limiter)
        response = await fetcher.get("/listings")

    assert response.status_code == 200
    assert response.json() == {"ok": True}
