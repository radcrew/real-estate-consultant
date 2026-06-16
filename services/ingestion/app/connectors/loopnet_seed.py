"""LoopNet seed connector: normalizes a local JSON dataset and upserts into Supabase."""

from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path
from typing import Any

from app.connectors.base import ConnectorBase, IngestionReport
from app.core.config import settings
from app.core.db_safe import execute_db_safe
from app.models.properties import Properties
from app.models.property_images import PropertyImages
from app.utils.values import clean_str_or_none, first_valid, round_or_none

# Stable UUID namespace keeps property IDs deterministic across re-seeds.
_PROPERTY_ID_NAMESPACE = uuid.UUID("018f3b2e-9c1a-7b3c-8f2d-6a5e4d3c2b1a")
_ACRE_TO_SQFT = 43_560.0
_CHUNK_SIZE = 500

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Parsing helpers (ported from backend/app/seed/parse.py)
# ---------------------------------------------------------------------------

def _parse_simple_float(text: str) -> float | None:
    t = text.strip()
    if not t:
        return None
    negative = t.startswith("-")
    if negative:
        t = t[1:].strip()
    num, dot_seen = "", False
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
            return t[len(symbol):].strip()
    return t


def _parse_money_string(s: str) -> float | None:
    t = _strip_leading_currency(s).replace(",", "")
    return _parse_simple_float(t) if t else None


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


def _parse_size_sqft(s: str) -> float | None:
    if not s.strip():
        return None
    value, tail = _take_leading_number(s)
    if value is None:
        return None
    t = tail.casefold().strip()
    if t.startswith("ac") or "acre" in t[:12]:
        return value * _ACRE_TO_SQFT
    compact = t.replace(" ", "")
    if t.startswith("sf") or "square" in t or "sqft" in compact or "sq.ft" in t or "sq. ft" in t:
        return value
    return None


def _to_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        return _parse_simple_float(stripped.replace(",", "")) if stripped else None
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


def _implied_monthly_rent(price: float | None) -> float | None:
    return (price * 0.05) / 12.0 if price is not None else None


def _implied_clear_height(size_sqft: float | None) -> float | None:
    if size_sqft is None or size_sqft <= 0:
        return None
    return min(22.0, max(14.0, 14.0 + min(8.0, size_sqft / 22_000.0)))


def _implied_loading_docks(size_sqft: float | None) -> int:
    return 2 if (size_sqft or 0.0) >= 35_000.0 else 1


def _parse_images(listing: dict[str, Any]) -> list[str]:
    raw = listing.get("KVImages")
    if not isinstance(raw, list):
        return []
    return [u for item in raw if isinstance(item, str) and (u := item.strip())]


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
        rent=round_or_none(_implied_monthly_rent(price_r), 2),
        clear_height=round_or_none(_implied_clear_height(size_sqft_v), 2),
        loading_docks=_implied_loading_docks(size_sqft_v),
    )


def _normalize(
    raw_rows: list[dict[str, Any]],
) -> tuple[list[tuple[Properties, list[PropertyImages]]], dict[str, int]]:
    rows: list[tuple[Properties, list[PropertyImages]]] = []
    rejected: dict[str, int] = {}
    for raw in raw_rows:
        prop_id_key = clean_str_or_none(raw.get("propertyId"))
        row_id = (
            uuid.uuid5(_PROPERTY_ID_NAMESPACE, f"loopnet:property:{prop_id_key.strip()}")
            if prop_id_key
            else None
        )
        prop = _parse_property(raw, row_id)
        if prop.address is None:
            rejected["missing_address"] = rejected.get("missing_address", 0) + 1
            continue
        images = (
            [PropertyImages(property_id=row_id, url=u) for u in _parse_images(raw)]
            if row_id is not None
            else []
        )
        rows.append((prop, images))
    return rows, rejected


# ---------------------------------------------------------------------------
# Connector
# ---------------------------------------------------------------------------

class LoopNetSeedConnector(ConnectorBase):
    """Loads a local JSON dataset and upserts listings into Supabase."""

    name = "loopnet-seed"

    async def run(self) -> IngestionReport:
        path = Path(settings.dataset_path)
        if not path.is_file():
            raise FileNotFoundError(f"Dataset not found: {path}")

        raw_rows: list[dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw_rows, list):
            raise ValueError("Dataset must be a JSON array")

        rows, rejected_reasons = _normalize(raw_rows)

        property_ids = [str(p.id) for p, _ in rows if p.id is not None]
        await self._delete_images(property_ids)
        await self._upsert_properties([p for p, _ in rows])
        image_rows = [img.model_dump(mode="json") for _, imgs in rows for img in imgs]
        await self._insert_images(image_rows)

        logger.info(
            "ingestion_run",
            extra={
                "source": self.name,
                "fetched": len(raw_rows),
                "normalized": len(rows),
                "rejected": len(raw_rows) - len(rows),
                "rejected_reasons": rejected_reasons,
            },
        )
        return IngestionReport(
            source=self.name,
            fetched=len(raw_rows),
            normalized=len(rows),
            rejected_reasons=rejected_reasons,
        )

    async def _delete_images(self, property_ids: list[str]) -> None:
        if not property_ids:
            return
        for start in range(0, len(property_ids), _CHUNK_SIZE):
            chunk = property_ids[start : start + _CHUNK_SIZE]
            await execute_db_safe(
                self._client.table("property_images").delete().in_("property_id", chunk).execute(),
            )

    async def _upsert_properties(self, rows: list[Properties]) -> None:
        if not rows:
            return
        payload = [r.model_dump(mode="json", exclude_none=True) for r in rows]
        for start in range(0, len(payload), _CHUNK_SIZE):
            chunk = payload[start : start + _CHUNK_SIZE]
            await execute_db_safe(
                self._client.table("properties").upsert(chunk, on_conflict="id").execute(),
            )

    async def _insert_images(self, rows: list[dict]) -> None:
        if not rows:
            return
        for start in range(0, len(rows), _CHUNK_SIZE):
            chunk = rows[start : start + _CHUNK_SIZE]
            await execute_db_safe(
                self._client.table("property_images").insert(chunk).execute(),
            )
