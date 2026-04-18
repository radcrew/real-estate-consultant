"""Parse listing dataset JSON into `Properties` rows."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from app.models.properties import Properties

logger = logging.getLogger(__name__)

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RAW_DATA_PATH = _BACKEND_ROOT / "dataset" / "raw-data.json"

_ACRE_TO_SQFT = 43_560.0


def load_listings(path: Path | None = None) -> list[dict[str, Any]]:
    """Parse the default (or given) raw JSON file: root must be an array of objects."""
    resolved = DEFAULT_RAW_DATA_PATH if path is None else path
    if not resolved.is_file():
        msg = f"Dataset file not found: {resolved}"
        raise FileNotFoundError(msg)

    data = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        msg = f"Expected a JSON array at root, got {type(data).__name__}"
        raise ValueError(msg)

    for i, item in enumerate(data):
        if not isinstance(item, dict):
            msg = f"Item at index {i} must be an object, got {type(item).__name__}"
            raise ValueError(msg)

    return data


def _blank_to_none(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else None
    text = str(value).strip()
    return text if text else None


def _parse_simple_float(text: str) -> float | None:
    """Parse a float: digits, optional commas, one ``.``, optional leading ``-``."""
    t = text.strip()
    if not t:
        return None
    negative = False
    if t.startswith("-"):
        negative = True
        t = t[1:].strip()
    num = ""
    dot_seen = False
    for ch in t:
        if ch.isdigit():
            num += ch
        elif ch == ",":
            continue
        elif ch == "." and not dot_seen:
            num += ch
            dot_seen = True
        else:
            break
    if not num or num == ".":
        return None
    try:
        value = float(num)
    except ValueError:
        return None
    return -value if negative else value


def _strip_leading_currency(text: str) -> str:
    t = text.strip()
    for symbol in ("$", "£", "€"):
        if t.startswith(symbol):
            return t[len(symbol) :].strip()
    return t


def _parse_money_string(s: str) -> float | None:
    t = _strip_leading_currency(s)
    if not t:
        return None
    t = t.replace(",", "")
    return _parse_simple_float(t)


def _take_leading_number(s: str) -> tuple[float | None, str]:
    """Leading number after optional ±/space; returns ``(value, rest_of_string)``."""
    i = 0
    while i < len(s) and s[i] in "± \t\n\r":
        i += 1
    parts: list[str] = []
    dot_seen = False
    while i < len(s):
        ch = s[i]
        if ch.isdigit():
            parts.append(ch)
        elif ch == ",":
            pass
        elif ch == "." and not dot_seen:
            parts.append(ch)
            dot_seen = True
        else:
            break
        i += 1
    raw = "".join(parts)
    if not raw or raw == ".":
        return None, s[i:]
    try:
        return float(raw), s[i:].strip()
    except ValueError:
        return None, s[i:].strip()


def _tail_means_acres(tail: str) -> bool:
    t = tail.casefold().strip()
    if t.startswith("ac"):
        return True
    head = t[:12]
    return "acre" in head


def _tail_means_sqft(tail: str) -> bool:
    t = tail.casefold().strip()
    if t.startswith("sf"):
        return True
    if "square" in t:
        return True
    compact = t.replace(" ", "")
    if "sqft" in compact:
        return True
    if "sq.ft" in t or "sq. ft" in t:
        return True
    return False


def _parse_size_sqft(s: str) -> float | None:
    """Parse size strings such as ``194,006 SF``, ``3.23 AC``, ``21,780-square-foot``."""
    if not s.strip():
        return None
    value, tail = _take_leading_number(s)
    if value is None:
        return None
    if _tail_means_acres(tail):
        return value * _ACRE_TO_SQFT
    if _tail_means_sqft(tail):
        return value
    return None


def _to_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        return _parse_simple_float(stripped.replace(",", ""))
    return None


def _best_size_sqft(raw: dict[str, Any]) -> float | None:
    sq = raw.get("squareFootage")
    if isinstance(sq, (int, float)):
        return float(sq)

    pf = raw.get("propertyFacts")
    if isinstance(pf, dict):
        for key in ("TotalBuildingSize", "TotalLotSize"):
            v = pf.get(key)
            if isinstance(v, str):
                got = _parse_size_sqft(v)
                if got is not None:
                    return got

    summary = raw.get("summary")
    if isinstance(summary, dict):
        for key in ("buildingSize", "grossLeasableArea", "lotSize", "floorSize"):
            v = summary.get(key)
            if isinstance(v, str):
                got = _parse_size_sqft(v)
                if got is not None:
                    return got

    bs = raw.get("buildingSize")
    if isinstance(bs, str):
        return _parse_size_sqft(bs)

    return None


def _best_price(raw: dict[str, Any]) -> float | None:
    pn = raw.get("priceNumeric")
    if isinstance(pn, (int, float)):
        return float(pn)

    p = raw.get("price")
    if isinstance(p, str):
        got = _parse_money_string(p)
        if got is not None:
            return got

    pf = raw.get("propertyFacts")
    if isinstance(pf, dict):
        pp = pf.get("Price")
        if isinstance(pp, str):
            return _parse_money_string(pp)

    return None


def _best_property_type(raw: dict[str, Any]) -> str | None:
    for key in ("propertyType", "propertyTypeDetailed"):
        got = _blank_to_none(raw.get(key))
        if got:
            return got
    summary = raw.get("summary")
    if isinstance(summary, dict):
        got = _blank_to_none(summary.get("propertyType"))
        if got:
            return got
    pf = raw.get("propertyFacts")
    if isinstance(pf, dict):
        for key in ("PropertyType", "PropertySubtype"):
            got = _blank_to_none(pf.get(key))
            if got:
                return got
    return None


def _round_num(value: float | None, places: int = 6) -> float | None:
    if value is None:
        return None
    return round(value, places)


def raw_to_properties(raw: dict[str, Any]) -> Properties:
    """Map one LoopNet-style listing object to a `Properties` row."""
    return Properties(
        address=_blank_to_none(raw.get("address")),
        city=_blank_to_none(raw.get("city")),
        state=_blank_to_none(raw.get("state")),
        country=_blank_to_none(raw.get("country")),
        latitude=_round_num(_to_float(raw.get("latitude")), 8),
        longitude=_round_num(_to_float(raw.get("longitude")), 8),
        property_type=_best_property_type(raw),
        listing_type=_blank_to_none(raw.get("listingType")),
        size_sqft=_round_num(_best_size_sqft(raw)),
        price=_round_num(_best_price(raw), 2),
        rent=None,
        clear_height=None,
        loading_docks=None,
    )


def load_properties(path: Path | None = None) -> list[Properties]:
    """Load the dataset file and return normalized `Properties` rows."""
    try:
        return [raw_to_properties(row) for row in load_listings(path)]
    except FileNotFoundError as exc:
        logger.warning("Seed: dataset file missing (%s)", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        logger.warning("Seed: invalid dataset (%s)", exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
