"""MCP tool helpers — always return content dicts; never raise to the host."""

from __future__ import annotations

import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from app.client.errors import AuthRequiredError

logger = logging.getLogger(__name__)


def ok_text(payload: Any) -> dict[str, Any]:
    text = payload if isinstance(payload, str) else json.dumps(payload, indent=2, default=str)
    return {"content": [{"type": "text", "text": text}]}


def error_text(message: str) -> dict[str, Any]:
    return {
        "isError": True,
        "content": [{"type": "text", "text": message}],
    }


async def run_backend(
    label: str,
    action: Callable[[], Awaitable[Any]],
    *,
    transform: Callable[[Any], Any] | None = None,
) -> dict[str, Any]:
    """Execute a backend call and map failures to MCP `isError` results."""
    try:
        data = await action()
        return ok_text(transform(data) if transform else data)
    except AuthRequiredError as exc:
        return error_text(str(exc))
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        body = (exc.response.text or "")[:300]
        logger.warning("%s HTTP %s: %s", label, status, body)
        if status == 401:
            return error_text("Unauthorized — check MCP_USER_ACCESS_TOKEN is a valid user JWT.")
        if status == 403:
            return error_text("Forbidden — this user cannot access that resource.")
        if status == 404:
            return error_text(f"Not found ({label}).")
        return error_text(f"Backend returned HTTP {status}: {body}")
    except httpx.RequestError as exc:
        logger.warning("%s request failed: %s", label, exc)
        return error_text(f"Could not reach backend: {exc}")
    except Exception as exc:  # noqa: BLE001 — surface to host, never crash stdio
        logger.exception("%s unexpected error", label)
        return error_text(f"Unexpected error: {exc}")


def compact_property(prop: dict[str, Any] | None) -> dict[str, Any]:
    p = prop or {}
    return {
        "property_id": p.get("id"),
        "address": p.get("address"),
        "city": p.get("city"),
        "state": p.get("state"),
        "country": p.get("country"),
        "property_type": p.get("property_type"),
        "listing_type": p.get("listing_type"),
        "price": p.get("price"),
        "rent": p.get("rent"),
        "size_sqft": p.get("size_sqft"),
        "clear_height": p.get("clear_height"),
        "loading_docks": p.get("loading_docks"),
        "broker": p.get("listing_broker_name"),
        "broker_email": p.get("listing_broker_email"),
        "broker_phone": p.get("listing_broker_phone"),
    }


def compact_search_response(data: dict[str, Any]) -> dict[str, Any]:
    results = []
    for item in data.get("results") or []:
        if not isinstance(item, dict):
            continue
        raw_prop = item.get("property")
        prop = raw_prop if isinstance(raw_prop, dict) else {}
        row = compact_property(prop)
        row["match_score"] = item.get("match_score")
        results.append(row)
    return {
        "criteria": data.get("criteria"),
        "total": data.get("total"),
        "limit": data.get("limit"),
        "offset": data.get("offset"),
        "results": results,
        "hint": "Call get_listing(property_id) for full detail on any result.",
    }


def compact_featured_response(data: dict[str, Any]) -> dict[str, Any]:
    listings = []
    for item in data.get("listings") or []:
        if not isinstance(item, dict):
            continue
        prop = item.get("property") if isinstance(item.get("property"), dict) else {}
        listings.append(compact_property(prop))
    return {"listings": listings, "count": len(listings)}


def compact_agent_response(data: dict[str, Any]) -> dict[str, Any]:
    props = []
    for prop in data.get("properties") or []:
        if isinstance(prop, dict):
            props.append(compact_property(prop))
    return {
        "name": data.get("name"),
        "email": data.get("email"),
        "phone": data.get("phone"),
        "listings_count": len(props),
        "listings": props,
    }
