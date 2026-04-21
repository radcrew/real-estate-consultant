"""Helpers for Supabase PostgREST ``.execute()`` result payloads."""

from __future__ import annotations

from fastapi import HTTPException, status


def as_row_list(raw: object) -> list[dict]:
    """Normalize ``result.data`` to a list of dict rows."""
    if isinstance(raw, dict):
        return [raw]
    if not isinstance(raw, list):
        return []
    return [r for r in raw if isinstance(r, dict)]


def require_single_row(raw: object, *, detail: str) -> dict:
    """Expect exactly one dict row; otherwise raise HTTP 502."""
    if isinstance(raw, dict):
        return raw

    if isinstance(raw, list):
        if len(raw) == 1 and isinstance(raw[0], dict):
            return raw[0]

    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)
