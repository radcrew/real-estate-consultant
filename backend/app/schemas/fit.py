"""API schemas for property fit explanations."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FitScoreBreakdown(BaseModel):
    """The three ranked match components plus the blended total (``match_score``)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    location: float = Field(..., ge=0.0, le=1.0)
    price: float = Field(..., ge=0.0, le=1.0)
    size: float = Field(..., ge=0.0, le=1.0)
    total: float = Field(..., ge=0.0, le=100.0)


class FitExplanationResponse(BaseModel):
    """Body for ``POST /api/v1/search/{session_profile_id}/fit/{property_id}``."""

    model_config = ConfigDict(str_strip_whitespace=True)

    property_id: UUID
    score: FitScoreBreakdown
    summary: str
    strengths: list[str] = Field(default_factory=list)
    considerations: list[str] = Field(default_factory=list)
