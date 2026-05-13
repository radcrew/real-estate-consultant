"""Prompt text and user-message assembly for broker outreach drafts."""

from __future__ import annotations

from typing import Any

OUTREACH_EMAIL_SYSTEM_PROMPT = (
    "You help users write concise, professional plain-text emails to commercial real estate "
    "listing brokers. Rules: use only facts from the listing summary provided; do not invent "
    "broker contact details, prices, or features; do not use markdown or HTML; keep a neutral, "
    "respectful tone suitable for the U.S. market."
)

OUTREACH_EMAIL_USER_INSTRUCTIONS = (
    "Write a draft email from the user to the listing broker about this property. "
    "If broker name is given, greet them by name; otherwise use a neutral greeting. "
    "The user wants to express interest and request a conversation or showing "
    "if appropriate.\n\n"
)

_LISTING_KEYS: tuple[str, ...] = (
    "address",
    "city",
    "state",
    "country",
    "listing_type",
    "property_type",
    "price",
    "rent",
    "size_sqft",
    "clear_height",
    "loading_docks",
    "description",
    "listing_broker_name",
    "listing_broker_email",
    "listing_broker_phone",
)


def format_listing_block_for_outreach(property_row: dict[str, Any]) -> str:
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


def build_outreach_user_message(*, property_row: dict[str, Any]) -> str:
    """Full user-role message: instructions plus listing summary."""
    block = format_listing_block_for_outreach(property_row)
    return f"{OUTREACH_EMAIL_USER_INSTRUCTIONS}Listing summary:\n{block}"
