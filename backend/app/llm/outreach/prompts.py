"""Prompt text and user-message assembly for broker outreach drafts."""

from __future__ import annotations

from typing import Any

OUTREACH_EMAIL_SYSTEM_PROMPT = (
    "You help users write concise, professional plain-text emails to commercial real estate "
    "listing brokers. Rules: use only facts from the listing summary and sender sections "
    "provided; do not invent broker contact details, prices, or features; do not use markdown "
    "or HTML; keep a neutral, respectful tone suitable for the U.S. market. When sender name "
    "or email is provided, use them in the body and sign-off as appropriate. Do not ask the "
    'sender to fill in placeholders such as "Your Full Name" or bracketed name prompts.'
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


def format_sender_block_for_outreach(
    *,
    profile_row: dict[str, Any] | None,
    auth_email: str | None,
) -> str:
    """Human-readable sender lines for the LLM (profiles + auth email fallback)."""
    parts: list[str] = []
    if profile_row is not None:
        for key in ("first_name", "last_name", "email"):
            value = profile_row.get(key)
            if value is None or value == "":
                continue
            parts.append(f"{key}: {value}")
    profile_email = (profile_row or {}).get("email") if profile_row else None
    has_profile_email = isinstance(profile_email, str) and profile_email.strip()
    if not has_profile_email and auth_email and str(auth_email).strip():
        parts.append(f"email: {str(auth_email).strip()}")
    if not parts:
        return (
            "(No sender name or email on file — use a brief neutral sign-off without "
            "inventing a name or asking the reader to supply one.)"
        )
    return "\n".join(parts)


def build_outreach_user_message(
    *,
    property_row: dict[str, Any],
    profile_row: dict[str, Any] | None = None,
    auth_email: str | None = None,
) -> str:
    """Full user-role message: instructions, optional sender context, plus listing summary."""
    listing_block = format_listing_block_for_outreach(property_row)
    sender_block = format_sender_block_for_outreach(profile_row=profile_row, auth_email=auth_email)
    return (
        f"{OUTREACH_EMAIL_USER_INSTRUCTIONS}"
        f"Sender (the person writing this email):\n{sender_block}\n\n"
        f"Listing summary:\n{listing_block}"
    )
