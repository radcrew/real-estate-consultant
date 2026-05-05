"""API models for property search."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, RootModel

from app.models.properties import Properties


class UpdateSearchCriteriaBody(RootModel[dict[str, Any]]):
    """Replace intake ``criteria``: keys are question keys; values are answers (any JSON shape)."""


class CriteriaFieldItem(BaseModel):
    """One criterion key with question metadata from ``questions`` plus stored value."""

    model_config = ConfigDict(str_strip_whitespace=True)
    type: str
    label: str
    data: Any

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
            "Intake session criteria: each key is wrapped with ``type``, ``label`` "
            "(from ``questions``) and ``data`` (stored value)."
        ),
    )
    results: list[PropertyMatch]
    total: int
    limit: int
    offset: int
