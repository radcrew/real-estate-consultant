"""Persistence for ``public.intake_parse_log`` (Supabase): one row per intake extraction.

The eval could not have caught any of the four bugs reported against a served adapter,
because it was written before they were known and nothing kept the turns that produced
them. Reconstructing them meant asking the user what they had typed. This is the table
that stops that happening again — a sampled row plus a gold label is an eval turn.

The write is deliberately best-effort. Telemetry that can fail a user's turn is worse
than no telemetry, so every failure here is logged and swallowed.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from supabase import AsyncClient

logger = logging.getLogger(__name__)

# Long enough for anything a person types into an intake box, short enough that a pasted
# document does not become a row nobody can read. Truncation is marked, never silent.
_MAX_INPUT_CHARS = 4000
_TRUNCATION_MARKER = "...[truncated]"


def _clip(text: str) -> str:
    if len(text) <= _MAX_INPUT_CHARS:
        return text
    return text[: _MAX_INPUT_CHARS - len(_TRUNCATION_MARKER)] + _TRUNCATION_MARKER


async def record_intake_parse(
    client: AsyncClient,
    *,
    session_id: UUID | None,
    user_input: str,
    current_criteria: dict[str, Any],
    model_output: dict[str, Any],
    extracted: dict[str, Any],
    unconfirmed_fields: list[str],
    missing_fields: list[str],
    model: str | None,
    temperature: float | None,
    latency_ms: int | None,
) -> None:
    """Record one extraction. Never raises, and never delays the caller's response.

    ``model_output`` is the reply before the criteria filters and ``extracted`` is what
    the session stored. Keeping both is what makes a filter regression visible: they were
    the same object until the evidence checks landed, and a row holding only the second
    cannot say whether the model or the filter is what changed.
    """
    if not (user_input or "").strip():
        return
    row = {
        "session_id": str(session_id) if session_id else None,
        "user_input": _clip(user_input),
        "current_criteria": current_criteria or {},
        "model_output": model_output or {},
        "extracted": extracted or {},
        "unconfirmed_fields": unconfirmed_fields or [],
        "missing_fields": missing_fields or [],
        "model": model,
        "temperature": temperature,
        "latency_ms": latency_ms,
    }
    try:
        await client.table("intake_parse_log").insert(row).execute()
    except Exception:
        # Deliberately broad. This runs after the user's answer is already computed, and
        # the failure modes are all environmental -- table not migrated yet, transient
        # network, a client bound to a project without it. None of them is a reason to
        # turn a working intake turn into a 500.
        logger.warning("intake_parse_log write failed", exc_info=True)
