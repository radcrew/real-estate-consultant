"""Parse intake search criteria dicts (no SQL / DB)."""

from __future__ import annotations

from typing import Any

LocationFields = tuple[str | None, str | None, str | None, str | None]


def float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def ilike_pattern(term: str) -> str:
    esc = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{esc}%"


def parse_range(bounds: Any) -> tuple[float | None, float | None]:
    if not isinstance(bounds, dict):
        return None, None
    return float_or_none(bounds.get("min")), float_or_none(bounds.get("max"))


def gaussian_target_sigma(lo: float | None, hi: float | None) -> tuple[float | None, float]:
    """Gaussian center and sigma (sigma >= 1), from intake ``min`` / ``max``."""
    if lo is not None and hi is not None:
        mid = (lo + hi) / 2.0
        span = abs(hi - lo)
        return mid, max(span / 2.0, 1.0)
    if lo is not None:
        return lo, max(abs(lo) * 0.15, 1.0)
    if hi is not None:
        return hi, max(abs(hi) * 0.15, 1.0)
    return None, 1.0


def parse_location_fields(criteria: dict[str, Any]) -> LocationFields:
    """Parse ``(label, city, state, country)`` from ``criteria["location"]``."""
    loc = criteria.get("location")
    if isinstance(loc, str):
        t = loc.strip()
        return (t if t else None), None, None, None
    if isinstance(loc, dict):

        def _s(key: str) -> str | None:
            v = loc.get(key)
            return v.strip() if isinstance(v, str) and v.strip() else None

        lab = _s("label")
        return lab, _s("city"), _s("state"), _s("country")
    return None, None, None, None
