from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from app.models.properties import Properties
from app.models.property_images import PropertyImages
from app.utils.values import clean_str_or_none, first_valid, round_or_none

# Stable UUID namespace for deterministic ``properties.id`` from source ``propertyId`` (seeding / FKs).
_PROPERTY_ID_NAMESPACE = uuid.UUID("018f3b2e-9c1a-7b3c-8f2d-6a5e4d3c2b1a")

logger = logging.getLogger(__name__)

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RAW_DATA_PATH = _BACKEND_ROOT / "dataset" / "raw-data.json"

_ACRE_TO_SQFT = 43_560.0


def parse_json_file(path: Path | None = None) -> list[dict[str, Any]]:
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


def _parse_simple_float(text: str) -> float | None:
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


def _best_size_sqft(listing: dict[str, Any]) -> float | None:
    sq = listing.get("squareFootage")
    if isinstance(sq, (int, float)):
        return float(sq)

    pf = listing.get("propertyFacts")
    if isinstance(pf, dict):
        for key in ("TotalBuildingSize", "TotalLotSize"):
            v = pf.get(key)
            if isinstance(v, str):
                got = _parse_size_sqft(v)
                if got is not None:
                    return got

    summary = listing.get("summary")
    if isinstance(summary, dict):
        for key in ("buildingSize", "grossLeasableArea", "lotSize", "floorSize"):
            v = summary.get(key)
            if isinstance(v, str):
                got = _parse_size_sqft(v)
                if got is not None:
                    return got

    bs = listing.get("buildingSize")
    if isinstance(bs, str):
        return _parse_size_sqft(bs)

    return None


def _best_price(listing: dict[str, Any]) -> float | None:
    pn = listing.get("priceNumeric")
    if isinstance(pn, (int, float)):
        return float(pn)

    p = listing.get("price")
    if isinstance(p, str):
        got = _parse_money_string(p)
        if got is not None:
            return got

    pf = listing.get("propertyFacts")
    if isinstance(pf, dict):
        pp = pf.get("Price")
        if isinstance(pp, str):
            return _parse_money_string(pp)

    return None


def _best_property_type(listing: dict[str, Any]) -> str | None:
    result = first_valid([listing.get(k) for k in ("propertyType", "propertyTypeDetailed")])
    if result:
        return result
    summary = listing.get("summary")
    if isinstance(summary, dict):
        got = clean_str_or_none(summary.get("propertyType"))
        if got:
            return got
    pf = listing.get("propertyFacts")
    if isinstance(pf, dict):
        got = first_valid([pf.get(k) for k in ("PropertyType", "PropertySubtype")])
        if got:
            return got
    return None


def _implied_monthly_rent_from_price(price: float | None) -> float | None:
    """Rough placeholder: assume ~5% annual gross on price, shown as monthly."""
    if price is None:
        return None
    return (price * 0.05) / 12.0


def _implied_clear_height_ft(size_sqft: float | None) -> float | None:
    """Larger footprints imply slightly higher typical clear height (simple curve)."""
    if size_sqft is None or size_sqft <= 0:
        return None
    # 14 ft at small bay scale → up to ~22 ft for large bulk buildings
    h = 14.0 + min(8.0, size_sqft / 22_000.0)
    return min(22.0, max(14.0, h))


def _implied_loading_docks(size_sqft: float | None) -> int:
    """Seed placeholder: most listings are 1–2 docks; scale lightly with size."""
    sq = 0.0 if size_sqft is None else float(size_sqft)
    return 2 if sq >= 35_000.0 else 1


def _property_id_from_key(property_id_key: str) -> uuid.UUID:
    return uuid.uuid5(_PROPERTY_ID_NAMESPACE, f"loopnet:property:{property_id_key.strip()}")


def _parse_images(listing: dict[str, Any]) -> list[str]:
    raw = listing.get("KVImages")
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    for item in raw:
        if isinstance(item, str):
            u = item.strip()
            if u:
                out.append(u)
    return out


def _parse_property(listing: dict[str, Any], row_id: uuid.UUID | None) -> Properties:
    size_sqft_v = _best_size_sqft(listing)
    price_v = _best_price(listing)
    size_r = round_or_none(size_sqft_v)
    price_r = round_or_none(price_v, 2)
    return Properties(
        id=row_id,
        address=clean_str_or_none(listing.get("address")),
        city=clean_str_or_none(listing.get("city")),
        state=clean_str_or_none(listing.get("state")),
        country=clean_str_or_none(listing.get("country")),
        latitude=round_or_none(_to_float(listing.get("latitude")), 8),
        longitude=round_or_none(_to_float(listing.get("longitude")), 8),
        property_type=_best_property_type(listing),
        listing_type=clean_str_or_none(listing.get("listingType")),
        description=clean_str_or_none(listing.get("description")),
        size_sqft=size_r,
        price=price_r,
        rent=round_or_none(_implied_monthly_rent_from_price(price_r), 2),
        clear_height=round_or_none(_implied_clear_height_ft(size_sqft_v), 2),
        loading_docks=_implied_loading_docks(size_sqft_v),
    )


def parse_listing_models(
    listing: dict[str, Any],
) -> tuple[Properties, list[PropertyImages]]:
    prop_id_key = clean_str_or_none(listing.get("propertyId"))
    row_id = _property_id_from_key(prop_id_key) if prop_id_key else None
    prop = _parse_property(listing, row_id)
    images: list[PropertyImages] = []
    if row_id is not None:
        images = [
            PropertyImages(property_id=row_id, url=u)
            for u in _parse_images(listing)
        ]
    return prop, images


def load_property_dataset(
    path: Path | None = None,
) -> list[tuple[Properties, list[PropertyImages]]]:
    try:
        return [parse_listing_models(row) for row in parse_json_file(path)]
    except FileNotFoundError as exc:
        logger.warning("Seed: dataset file missing (%s)", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        logger.warning("Seed: invalid dataset (%s)", exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
