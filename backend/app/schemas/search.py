"""API models for property search."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.properties import Properties


class CriteriaFieldItem(BaseModel):
    """One criterion key with question ``type`` from ``questions`` plus stored value."""

    model_config = ConfigDict(str_strip_whitespace=True)

    type: str = Field(
        ...,
        description="``questions.type`` for the question row whose ``key`` matches this criterion.",
    )
    data: Any = Field(..., description="Value stored on the intake session for this criterion key.")


class PropertyMatch(BaseModel):
    """One property row plus LLM match score (0–100)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    property: Properties
    match_score: float = Field(..., ge=0.0, le=100.0)


class SearchPropertiesResponse(BaseModel):
    """Body for ``GET /api/v1/search``."""

    model_config = ConfigDict(str_strip_whitespace=True)

    criteria: dict[str, CriteriaFieldItem] = Field(
        default_factory=dict,
        description=(
            "Intake session criteria: each key is wrapped with ``type`` "
            "(from ``questions``) and ``data`` (stored value)."
        ),
    )
    results: list[PropertyMatch]
    total: int
    limit: int
    offset: int
