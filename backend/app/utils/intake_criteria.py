"""Normalize intake answers into the flat storage format search expects."""

from __future__ import annotations

from typing import Any

from app.utils.values import clean_str_or_none

_LOCATION_TYPES = frozenset({"location", "geo", "address"})
_MULTI_SELECT_TYPES = frozenset(
    {"multiselect", "multi_select", "multi-select", "tags", "checkboxes", "building_types"},
)
_RANGE_TYPES = frozenset(
    {"range", "numeric_range", "sqft_range", "rent_range", "size_range"},
)


def _normalize_location(value: Any) -> str | Any:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        parts = [
            part
            for key in ("city", "state", "country")
            if (part := clean_str_or_none(value.get(key)))
        ]
        if parts:
            return ", ".join(parts)
        for key in ("label", "input"):
            if text := clean_str_or_none(value.get(key)):
                return text
    return value


def _normalize_multi_select(value: Any) -> list[str]:
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    if isinstance(value, list):
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]
    return []


def _normalize_range(value: Any) -> dict[str, Any] | Any:
    if not isinstance(value, dict):
        return value
    out: dict[str, Any] = {}
    for key in ("min", "max"):
        raw = value.get(key)
        if raw is None:
            continue
        try:
            out[key] = float(raw)
        except (TypeError, ValueError):
            continue
    unit = value.get("unit")
    if isinstance(unit, str) and unit.strip():
        out["unit"] = unit.strip()
    return out or value


def normalize_intake_value(question_type: str, value: Any) -> Any:
    """Coerce LLM or guided answers into stored criteria values."""
    qtype = question_type.strip().lower() if isinstance(question_type, str) else "text"

    if qtype in _LOCATION_TYPES:
        return _normalize_location(value)
    if qtype in _MULTI_SELECT_TYPES:
        return _normalize_multi_select(value)
    if qtype in _RANGE_TYPES:
        return _normalize_range(value)
    return value


def normalize_merged_criteria(
    merged_criteria: dict[str, Any],
    questions: list[dict[str, Any]],
    *,
    reserved_keys: frozenset[str] | None = None,
) -> dict[str, Any]:
    """Normalize every answered question key in ``merged_criteria``."""
    reserved = reserved_keys or frozenset()
    type_by_key = {
        row["key"]: row["type"]
        for row in questions
        if isinstance(row.get("key"), str) and isinstance(row.get("type"), str)
    }
    normalized: dict[str, Any] = {}
    for key, value in merged_criteria.items():
        if key in reserved:
            normalized[key] = value
            continue
        normalized[key] = normalize_intake_value(type_by_key.get(key, "text"), value)
    return normalized
