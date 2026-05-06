"""API models for property search."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel

from app.models.properties import Properties


class UpdateSearchCriteriaBody(RootModel[dict[str, Any]]):
    """Replace intake ``criteria``: keys are question keys; values are answers (any JSON shape)."""


class CriteriaFieldItem(BaseModel):
    """Question-backed criterion: ``type`` / ``label`` always; ``data`` only when answered."""

    model_config = ConfigDict(str_strip_whitespace=True)

    type: str = Field(..., description="``questions.type`` for this key.")
    label: str = Field(default="", description="``questions.title`` for this key.")
    unit: str | None = Field(
        default=None,
        description="From ``questions.options.unit`` for range-style types only.",
    )
    data: Any | None = Field(
        default=None,
        description="Stored answer when present; omitted when not set.",
    )


class SearchCriteriaUpdateResponse(BaseModel):
    """Intake session after replacing criteria (same ``criteria`` envelope as GET ``/search``)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: UUID | None = None
    status: str = Field(default="in_progress")
    created_at: AwareDatetime | None = None
    search_profile_id: UUID | None = None
    criteria: dict[str, CriteriaFieldItem] = Field(
        default_factory=dict,
        description="Per key: ``type``, ``label``, optional ``unit``; ``data`` if answered.",
    )


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
            "All configured question keys from ``questions``: ``type`` and ``label`` "
            "always; ``unit`` for range-style types when ``options.unit`` is set; "
            "``data`` present only when that key exists on the session criteria."
        ),
    )
    results: list[PropertyMatch]
    total: int
    limit: int
    offset: int
