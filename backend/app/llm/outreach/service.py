"""Outreach orchestration: LLM provider calls for broker email drafts."""

from __future__ import annotations

from typing import Any

from app.llm.outreach.exceptions import raise_outreach_email_empty
from app.llm.outreach.prompts import OUTREACH_EMAIL_SYSTEM_PROMPT, build_outreach_user_message
from app.llm.outreach.schema import OutreachDraftEmailLLM
from app.llm.providers import huggingface_provider


async def generate_broker_outreach_draft(
    *,
    property_row: dict[str, Any],
    profile_row: dict[str, Any] | None = None,
    auth_email: str | None = None,
) -> str:
    """Return a plain-text broker outreach email draft (not persisted)."""
    user_content = build_outreach_user_message(
        property_row=property_row,
        profile_row=profile_row,
        auth_email=auth_email,
    )
    messages = [
        {"role": "system", "content": OUTREACH_EMAIL_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
    parsed = await huggingface_provider.generate_structured_output(
        messages=messages,
        response_format=OutreachDraftEmailLLM,
        temperature=0.35,
        max_tokens=2048,
    )
    text = parsed.draft_email.strip()
    if not text:
        raise_outreach_email_empty()
    return text
