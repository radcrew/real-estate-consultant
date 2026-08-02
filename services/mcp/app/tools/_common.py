"""MCP tool helpers — always return content dicts; never raise to the host."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from app.auth import AuthInvalidError, AuthRequiredError
from app.config import settings
from app.middleware import RateLimitError, SlidingWindowRateLimiter, sanitize_tool_text
from app.middleware.sanitize import redact_secrets

logger = logging.getLogger(__name__)

_rate_limiter = SlidingWindowRateLimiter(
    max_calls=settings.rate_limit_per_minute,
    window_seconds=60.0,
)


def ok_text(payload: Any) -> dict[str, Any]:
    text = payload if isinstance(payload, str) else json.dumps(payload, indent=2, default=str)
    text = sanitize_tool_text(text, max_chars=settings.max_tool_output_chars)
    return {"content": [{"type": "text", "text": text}]}


def error_text(message: str) -> dict[str, Any]:
    text = sanitize_tool_text(message, max_chars=2_000)
    return {
        "isError": True,
        "content": [{"type": "text", "text": text}],
    }


async def run_backend(
    label: str,
    action: Callable[[], Awaitable[Any]],
    *,
    transform: Callable[[Any], Any] | None = None,
) -> dict[str, Any]:
    """Execute a backend call and map failures to MCP `isError` results."""
    try:
        _rate_limiter.acquire()
        data = await asyncio.wait_for(action(), timeout=settings.http_timeout_seconds)
        return ok_text(transform(data) if transform else data)
    except RateLimitError as exc:
        return error_text(str(exc))
    except TimeoutError:
        logger.warning("%s timed out after %ss", label, settings.http_timeout_seconds)
        return error_text(
            f"Timed out calling backend after {settings.http_timeout_seconds:.0f}s ({label}).",
        )
    except AuthRequiredError as exc:
        return error_text(str(exc))
    except AuthInvalidError as exc:
        return error_text(str(exc))
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        body = redact_secrets((exc.response.text or "")[:300])
        logger.warning("%s HTTP %s: %s", label, status, body)
        if status == 401:
            return error_text(str(AuthInvalidError()))
        if status == 403:
            return error_text(
                "Forbidden — this user cannot access that resource.",
            )
        if status == 404:
            return error_text(f"Not found ({label}).")
        if status == 429:
            return error_text(
                "Rate limited by the backend (MCP API key or server limit). "
                "Wait a moment and retry.",
            )
        if status in {502, 503, 504}:
            return error_text(
                f"Backend unavailable (HTTP {status}) for {label}. "
                "Often a cold start or upstream outage — retry once.",
            )
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


def compact_similar_response(data: dict[str, Any]) -> dict[str, Any]:
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
        "results": results,
        "count": len(results),
        "limit": data.get("limit"),
        "hint": "Call get_listing(property_id) for full detail on any result.",
    }
