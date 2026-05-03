"""API models for property search."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.properties import Properties


class PropertyMatch(BaseModel):
    """One property row plus LLM match score (0–100)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    property: Properties
    match_score: float = Field(..., ge=0.0, le=100.0)


class SearchPropertiesResponse(BaseModel):
    """Body for ``GET /api/v1/search``."""

    model_config = ConfigDict(str_strip_whitespace=True)

    criteria: dict[str, Any] = Field(
        default_factory=dict,
        description="Intake session ``criteria`` used for semantic scoring.",
    )
    results: list[PropertyMatch]
    total: int
    limit: int
    offset: int
