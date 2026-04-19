"""Helpers for awaiting Supabase PostgREST calls with consistent error handling."""

from __future__ import annotations

import logging
from collections.abc import Awaitable
from typing import TypeVar

import httpx
from postgrest.exceptions import APIError

logger = logging.getLogger(__name__)

T = TypeVar("T")


class SupabaseRequestError(RuntimeError):
    """Raised when a Supabase PostgREST call fails (API error or HTTP transport failure)."""


async def execute_db_safe(awaitable: Awaitable[T]) -> T:
    """Await a Supabase client chain ending in ``.execute()`` and normalize failures.

    Use for any code path that talks to PostgREST via the async Supabase Python client
    (table builders, RPC, etc.).
    """
    try:
        return await awaitable
    except APIError as exc:
        logger.error("Supabase PostgREST error: %s", exc)
        err_text = str(exc).lower()
        if "pgrst204" in err_text or "schema cache" in err_text:
            logger.error(
                "Hint: PostgREST schema cache may be stale or a column may be missing. "
                "Apply migrations, then SQL Editor: NOTIFY pgrst, 'reload schema';"
            )
        raise SupabaseRequestError(f"Supabase (PostgREST): {exc}") from exc
    except httpx.HTTPError as exc:
        logger.error("HTTP error talking to Supabase: %s", exc)
        raise SupabaseRequestError(
            "Could not reach Supabase (check SUPABASE_URL, network, and that the "
            f"project is running): {exc}"
        ) from exc
