"""Helpers for formatting intake criteria in API responses (e.g. property search)."""

from __future__ import annotations

from typing import Any

from supabase import AsyncClient

from app.repositories.questions import load_question_key_metadata
from app.schemas.search import CriteriaFieldItem


async def normalize_criteria(
    client: AsyncClient,
    criteria: dict[str, Any],
) -> dict[str, CriteriaFieldItem]:
    """Merge session ``criteria`` with every configured question key (insertion order preserved).

    Keys follow ``key_to_type`` order (same as ``questions.order_index`` fetch order).
    Missing answers use ``data=None`` (omit from JSON when route uses exclude_none).
    Session-only keys not in ``questions`` are appended with ``type`` ``unknown``.
    """
    out: dict[str, CriteriaFieldItem] = {}

    types, titles = await load_question_key_metadata(client)

    for key in types:
        qtype = types[key]
        label = titles[key]
        if key in criteria:
            out[key] = CriteriaFieldItem(type=qtype, label=label, data=criteria[key])
        else:
            out[key] = CriteriaFieldItem(type=qtype, label=label, data=None)

    for key, value in criteria.items():
        if key not in out:
            out[key] = CriteriaFieldItem(type="unknown", label="", data=value)

    return out
