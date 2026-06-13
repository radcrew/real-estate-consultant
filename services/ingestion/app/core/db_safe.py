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
    try:
        return await awaitable
    except APIError as exc:
        logger.error("Supabase PostgREST error: %s", exc)
        raise SupabaseRequestError(f"Supabase (PostgREST): {exc}") from exc
    except httpx.HTTPError as exc:
        logger.error("HTTP error talking to Supabase: %s", exc)
        raise SupabaseRequestError(f"Could not reach Supabase: {exc}") from exc
