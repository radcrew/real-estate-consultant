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
_SINGLE_SELECT_TYPES = frozenset({"select", "single_choice", "radio"})


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


def _configured_options(row: dict[str, Any]) -> list[str]:
    """Configured choices for a question, or [] when it does not have a fixed set.

    Range questions carry ``options`` as a dict (``{"unit": "USD"}``), so only a list is
    an enumeration.
    """
    options = row.get("options")
    if not isinstance(options, list):
        return []
    return [choice for choice in options if isinstance(choice, str) and choice.strip()]


def _canonical_choice(value: str, options: list[str]) -> str | None:
    """The configured spelling of ``value``, or None when it is not a configured choice."""
    folded = value.strip().casefold()
    return next((choice for choice in options if choice.casefold() == folded), None)


def _is_option_dump(chosen: list[str], options: list[str]) -> bool:
    """True when a multi-select answer is simply the whole option list.

    Free text never means "office, retail, industrial, warehouse, flex and land" — that
    is the model copying the schema's choices into the answer, which the prompt rules
    already forbid and the stock model does constantly. Two-choice questions are excluded
    because "buy or lease" genuinely can be both.
    """
    return len(options) > 2 and {c.casefold() for c in chosen} == {o.casefold() for o in options}


def drop_unconfigured_choices(
    extracted: dict[str, Any],
    questions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Remove select / multi-select answers that are not offered by the questionnaire.

    The intake service filters extracted keys against ``question_keys`` but never checks
    values, so ``property_type: ["house"]`` — a type this questionnaire does not offer —
    is stored, counted as answered, and handed to the SQL filter. Dropping the key
    instead leaves the field missing, so it gets asked again.

    Values differing only in case are kept and canonicalised to the configured spelling.
    """
    rows_by_key = {row["key"]: row for row in questions if isinstance(row.get("key"), str)}

    cleaned: dict[str, Any] = {}
    for key, value in extracted.items():
        row = rows_by_key.get(key)
        if row is None:
            cleaned[key] = value
            continue

        qtype = row.get("type")
        qtype = qtype.strip().lower() if isinstance(qtype, str) else "text"
        options = _configured_options(row)
        if not options or qtype not in (_MULTI_SELECT_TYPES | _SINGLE_SELECT_TYPES):
            cleaned[key] = value
            continue

        if qtype in _MULTI_SELECT_TYPES:
            chosen = [
                canonical
                for item in _normalize_multi_select(value)
                if (canonical := _canonical_choice(item, options)) is not None
            ]
            if chosen and not _is_option_dump(chosen, options):
                cleaned[key] = chosen
            continue

        if isinstance(value, str) and (canonical := _canonical_choice(value, options)):
            cleaned[key] = canonical

    return cleaned


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
