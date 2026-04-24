from __future__ import annotations

from typing import Any


def first_non_none(*values: Any) -> Any | None:
    """Return the first argument that is not ``None``."""
    return next((v for v in values if v is not None), None)


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


def to_str_list(value: Any) -> list[str]:
    """Coerce a scalar or list into a list of non-empty stripped strings."""
    if isinstance(value, list):
        return [s for v in value if (s := str(v).strip())]
    if isinstance(value, str) and (s := value.strip()):
        return [s]
    return []


def try_float(value: Any) -> float | None:
    """Parse int/float/str to float; return None if not parseable."""
    if isinstance(value, (int, float, str)):
        try:
            return float(value if not isinstance(value, str) else value.strip())
        except (ValueError, TypeError):
            return None
    return None
