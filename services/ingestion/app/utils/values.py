from __future__ import annotations

from typing import Any


def clean_str_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def first_valid(values: list[Any]) -> str | None:
    for v in values:
        if cleaned := clean_str_or_none(v):
            return cleaned
    return None


def round_or_none(value: float | None, places: int = 6) -> float | None:
    if value is None:
        return None
    return round(value, places)
