"""API models for property search."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel

from app.models.properties import Properties


class QuickSearchBody(BaseModel):
    location: str | None = None
    property_types: list[str] = Field(default_factory=list)
    price_min: int | None = None
    price_max: int | None = None


class QuickSearchResponse(BaseModel):
    search_profile_id: UUID


class UpdateSearchCriteriaBody(RootModel[dict[str, Any]]):
    """Replace intake ``criteria``: keys are question keys; values are answers (any JSON shape)."""


class CriteriaFieldItem(BaseModel):
    """Question-backed criterion: ``type`` / ``label`` always; ``data`` only when answered."""

    model_config = ConfigDict(str_strip_whitespace=True)

    type: str
    label: str
    unit: str | None
    data: Any | None


class SearchCriteriaUpdateResponse(BaseModel):
    """Intake session after replacing criteria (same ``criteria`` envelope as GET ``/search``)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: UUID | None = None
    status: str = Field(default="in_progress")
    created_at: AwareDatetime | None = None
    search_profile_id: UUID | None = None
    criteria: dict[str, CriteriaFieldItem] = Field(default_factory=dict)


class PropertyMatch(BaseModel):
    """One property row plus LLM match score (0–100)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    property: Properties
    match_score: float = Field(..., ge=0.0, le=100.0)


class SearchPropertiesResponse(BaseModel):
    """Body for ``GET /api/v1/search``."""

    model_config = ConfigDict(str_strip_whitespace=True)

    criteria: dict[str, CriteriaFieldItem] = Field(default_factory=dict)
    results: list[PropertyMatch]
    total: int
    limit: int
    offset: int
