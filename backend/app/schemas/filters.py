"""API models for intake-derived filter metadata."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class FilterResponse(BaseModel):
    """Single filter definition keyed by intake ``questions.key``."""

    model_config = ConfigDict(str_strip_whitespace=True)

    type: str
    label: str
