"""Pydantic models for Hugging Face structured completion (fit explanations)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class FitExplanationLLM(BaseModel):
    """Structured LLM output explaining a property's match score."""

    summary: str = Field(
        ...,
        min_length=20,
        max_length=1000,
        description=(
            "1-3 sentence, plain-English explanation of why this property does or "
            "doesn't fit the stated criteria. No markdown, no restating the raw "
            "percentage."
        ),
    )
    strengths: list[str] = Field(
        default_factory=list,
        max_length=3,
        description="Up to 3 short phrases on what matches well.",
    )
    considerations: list[str] = Field(
        default_factory=list,
        max_length=3,
        description="Up to 3 short phrases on what doesn't match as well (never invented).",
    )
