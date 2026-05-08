"""Parse intake search criteria dicts (no SQL / DB)."""

from __future__ import annotations

from typing import Any

from app.utils.values import clean_str_or_none, float_or_none

LocationFields = tuple[str | None, str | None, str | None, str | None]

_COUNTRY_ALIASES: dict[str, str] = {
    "us": "US",
    "usa": "US",
    "united states": "US",
    "united states of america": "US",
}

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


def _normalize_country(country: str | None) -> str | None:
    if not country:
        return None
    key = country.strip().lower()
    return _COUNTRY_ALIASES.get(key, country)


def parse_location_fields(criteria: dict[str, Any]) -> LocationFields:
    """Parse ``(label, city, state, country)`` from ``criteria["location"]``."""
    location = criteria.get("location")

    if isinstance(location, str):
        label = clean_str_or_none(location)
        if not label:
            return None, None, None, None
        parts = [clean_str_or_none(part) for part in label.split(",")]
        tokens = [part for part in parts if part]
        if len(tokens) >= 3:
            return label, tokens[0], tokens[-2], _normalize_country(tokens[-1])
        if len(tokens) == 2:
            return label, tokens[0], None, _normalize_country(tokens[1])
        return label, None, None, None

    if isinstance(location, dict):
        label = clean_str_or_none(location.get("label"))
        city = clean_str_or_none(location.get("city"))
        state = clean_str_or_none(location.get("state"))
        country = _normalize_country(clean_str_or_none(location.get("country")))
        return label, city, state, country

    return None, None, None, None
