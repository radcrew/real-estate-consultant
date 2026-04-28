"""Reusable HTTP helpers for LLM provider integrations."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
from fastapi import HTTPException, status


async def post_json(
    *,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout: httpx.Timeout,
    retries: int,
    retry_base_delay_s: float,
    error_prefix: str,
) -> httpx.Response:
    """POST JSON with connect-level retries and normalized HTTPException errors."""
    last_exception: httpx.HTTPError | None = None

    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                return response
        except (httpx.ConnectTimeout, httpx.ConnectError) as exc:
            last_exception = exc
            if attempt + 1 < retries:
                await asyncio.sleep(retry_base_delay_s * (2**attempt))
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"{error_prefix}: {exc}",
            ) from exc

    assert last_exception is not None
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"{error_prefix} after retries: {last_exception}",
    ) from last_exception
