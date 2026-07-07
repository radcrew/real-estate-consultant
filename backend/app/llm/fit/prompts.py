"""Prompt text and user-message assembly for property fit explanations."""

from __future__ import annotations

import json
from typing import Any

from app.utils.criteria_search import parse_location_fields, parse_range

FIT_EXPLANATION_SYSTEM_PROMPT = (
    "You explain to a commercial real estate buyer or tenant why a specific listing "
    "scored the way it did against their stated search criteria. Rules: use only "
    "the criteria, listing facts, and match tiers provided; never invent numbers, "
    "addresses, or features; do not restate the raw match percentage; when a "
    "criterion is 'not specified', say so plainly rather than calling it a match; "
    "keep a neutral, factual tone; no markdown or HTML."
)

_TIER_THRESHOLDS: tuple[tuple[float, str], ...] = (
    (0.85, "excellent match"),
    (0.6, "good match"),
    (0.3, "partial match"),
    (0.0, "weak match"),
)


def score_to_tier(value: float, *, specified: bool) -> str:
    """Qualitative label for a 0.0-1.0 component score.

    Hands the LLM a label instead of a raw float, and distinguishes "the user
    never set this criterion" from "this happens to score well" -- both are
    1.0 in the underlying Gaussian, but only one is actually a match worth
    describing as such.
    """
    if not specified:
        return "not specified"
    if value <= 0.0:
        return "no match"
    for threshold, label in _TIER_THRESHOLDS:
        if value >= threshold:
            return label
    return "no match"


def _location_specified(criteria: dict[str, Any]) -> bool:
    return any(parse_location_fields(criteria))


def _range_specified(criteria: dict[str, Any], key: str) -> bool:
    lo, hi = parse_range(criteria.get(key))
    return lo is not None or hi is not None


def format_score_block_for_fit(
    criteria: dict[str, Any],
    *,
    location_score: float,
    price_score: float,
    size_score: float,
) -> str:
    """Plain-text score tiers for the three ranked match components."""
    lines = [
        f"location: {score_to_tier(location_score, specified=_location_specified(criteria))}",
        f"price: {score_to_tier(price_score, specified=_range_specified(criteria, 'price'))}",
        f"size: {score_to_tier(size_score, specified=_range_specified(criteria, 'size_sqft'))}",
    ]
    return "\n".join(lines)


_CRITERIA_KEYS: tuple[str, ...] = ("location", "price", "size_sqft", "property_type")

_LISTING_KEYS: tuple[str, ...] = (
    "address",
    "city",
    "state",
    "country",
    "property_type",
    "listing_type",
    "price",
    "rent",
    "size_sqft",
    "clear_height",
    "loading_docks",
    "description",
)


def format_criteria_block_for_fit(criteria: dict[str, Any]) -> str:
    """Serialize the criteria keys the match score is actually based on."""
    parts: list[str] = []
    for key in _CRITERIA_KEYS:
        value = criteria.get(key)
        if value is None or value == "" or value == {}:
            continue
        rendered = json.dumps(value) if isinstance(value, dict) else value
        parts.append(f"{key}: {rendered}")
    if not parts:
        return "(No search criteria set yet.)"
    return "\n".join(parts)


def format_listing_block_for_fit(property_row: dict[str, Any]) -> str:
    """Serialize known property keys into a plain-text block for the user message."""
    parts: list[str] = []
    for key in _LISTING_KEYS:
        value = property_row.get(key)
        if value is None or value == "":
            continue
        parts.append(f"{key}: {value}")
    if not parts:
        return "(No listing details provided.)"
    return "\n".join(parts)


def build_fit_user_message(
    *,
    criteria: dict[str, Any],
    property_row: dict[str, Any],
    location_score: float,
    price_score: float,
    size_score: float,
) -> str:
    """Full user-role message: instructions, criteria, listing, and score tiers."""
    criteria_block = format_criteria_block_for_fit(criteria)
    listing_block = format_listing_block_for_fit(property_row)
    score_block = format_score_block_for_fit(
        criteria,
        location_score=location_score,
        price_score=price_score,
        size_score=size_score,
    )
    return (
        "Explain briefly why this listing does or doesn't match the buyer's "
        "search criteria. Ground your explanation in the match tiers below; use "
        "listing facts only to make it concrete.\n\n"
        f"Search criteria:\n{criteria_block}\n\n"
        f"Listing:\n{listing_block}\n\n"
        f"Match tiers:\n{score_block}"
    )
