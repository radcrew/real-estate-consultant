"""Safe execution of async Supabase/PostgREST calls for seed (maps errors to HTTP responses)."""

from __future__ import annotations

import logging
from collections.abc import Awaitable
from typing import TypeVar

import httpx
from fastapi import HTTPException
from postgrest.exceptions import APIError

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def execute_db_safe(awaitable: Awaitable[T]) -> T:
    try:
        return await awaitable
    except APIError as exc:
        logger.error("Seed: Supabase PostgREST error: %s", exc)
        err_text = str(exc).lower()
        if "pgrst204" in err_text or "schema cache" in err_text:
            logger.error(
                "Seed: hint - PostgREST schema cache stale or column missing. "
                "Apply migrations, then SQL Editor: NOTIFY pgrst, 'reload schema';"
            )
        raise HTTPException(status_code=502, detail=f"Supabase (PostgREST): {exc}") from exc
    except httpx.HTTPError as exc:
        logger.error("Seed: HTTP error talking to Supabase: %s", exc)
        raise HTTPException(
            status_code=502,
            detail=(
                "Could not reach Supabase (check SUPABASE_URL, network, and that the "
                f"project is running): {exc}"
            ),
        ) from exc
