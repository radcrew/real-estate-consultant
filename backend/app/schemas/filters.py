"""API models for intake-derived filter metadata."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class FilterResponse(BaseModel):
    """Single filter definition keyed by intake ``questions.key``."""

    model_config = ConfigDict(str_strip_whitespace=True)

    type: str = Field(..., description="``questions.type``.")
    label: str = Field(
        default="",
        description="``questions.title`` (display label).",
    )
