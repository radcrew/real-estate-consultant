"""Helpers for formatting intake criteria in API responses (e.g. property search)."""

from __future__ import annotations

from typing import Any

from app.schemas.search import CriteriaFieldItem


def wrap_criteria_for_search_response(
    criteria: dict[str, Any],
    key_to_type: dict[str, str],
    key_to_title: dict[str, str],
) -> dict[str, CriteriaFieldItem]:
    """Wrap each ``criteria`` entry using ``questions`` key → type and key → title maps."""
    return {
        key: CriteriaFieldItem(
            type=key_to_type.get(key, "unknown"),
            label=key_to_title.get(key, ""),
            data=value,
        )
        for key, value in criteria.items()
    }
