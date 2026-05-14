"""Pydantic models for Hugging Face structured completion (outreach drafts)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class OutreachDraftEmailLLM(BaseModel):
    """Structured LLM output for a single plain-text email draft."""

    draft_email: str = Field(
        ...,
        min_length=20,
        max_length=16000,
        description=(
            "Complete plain-text email to the listing broker: greeting, 2–4 short paragraphs, "
            "clear ask, sign-off. No markdown or HTML."
        ),
    )
