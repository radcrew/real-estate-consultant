"""Normalize questionnaire ``criteria`` into ``search_profiles.filters``.

Canonical ``intake_sessions.criteria`` (flat JSON)::

    {
      "location": "Los Angeles",
      "property_type": "industrial",
      "min_size_sqft": 5000,
      "max_price": 2000000,
      "min_clear_height": 28,
      "min_loading_docks": 2
    }
"""

from __future__ import annotations

from typing import Any

from app.utils.values import clean_str_or_none, try_float


def normalize_intake_criteria(criteria: object) -> dict[str, Any]:
    """Map session ``criteria`` into a stable ``search_profiles.filters`` payload."""
    if not isinstance(criteria, dict):
        return {"raw_criteria": criteria}

    out: dict[str, Any] = {}

    if (loc := clean_str_or_none(criteria.get("location"))) is not None:
        out["location"] = loc

    if (pt := clean_str_or_none(criteria.get("property_type"))) is not None:
        out["property_type"] = pt

    for num_key in ("min_size_sqft", "max_price", "min_clear_height"):
        fv = try_float(criteria.get(num_key))
        if fv is not None:
            out[num_key] = fv

    docks = try_float(criteria.get("min_loading_docks"))
    if docks is not None:
        out["min_loading_docks"] = int(docks)

    return {k: v for k, v in out.items() if v is not None}
