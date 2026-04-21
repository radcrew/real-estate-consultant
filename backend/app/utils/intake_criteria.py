"""Normalize questionnaire ``criteria`` into search filter payloads."""

from __future__ import annotations

from typing import Any

from app.utils.values import first_non_none, to_str_list, try_float


def normalize_intake_criteria(criteria: object) -> dict[str, Any]:
    """Convert flexible intake criteria into a stable filter payload."""
    if not isinstance(criteria, dict):
        return {"raw_criteria": criteria}

    def str_list_from_keys(*keys: str) -> list[str]:
        return to_str_list(first_non_none(*(criteria.get(k) for k in keys)))

    def float_from_keys(*keys: str) -> float | None:
        for k in keys:
            val = try_float(criteria.get(k))
            if val is not None:
                return val
        return None

    def normalize_lower_str(val: object) -> str | None:
        if isinstance(val, str):
            s = val.strip().lower()
            return s or None
        return None

    normalized: dict[str, Any] = {
        "property_types": str_list_from_keys("property_types", "propertyType", "type"),
        "geography": str_list_from_keys("markets", "geography", "location"),
        "deal_type": normalize_lower_str(
            first_non_none(criteria.get("sale_or_lease"), criteria.get("deal_type")),
        ),
        "min_building_size_sf": float_from_keys("min_building_size_sf", "min_size_sf", "min_size"),
        "min_clear_height_ft": float_from_keys("min_clear_height_ft", "clear_height_ft"),
        "price_min": try_float(criteria.get("price_min")),
        "price_max": try_float(criteria.get("price_max")),
        "special_requirements": first_non_none(
            criteria.get("special_requirements"),
            criteria.get("requirements"),
            criteria.get("notes"),
        ),
        "raw_criteria": criteria,
    }

    return {k: v for k, v in normalized.items() if v is not None}
