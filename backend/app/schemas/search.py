"""API models for property search."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.properties import Properties


class SearchPropertiesResponse(BaseModel):
    """Body for ``GET /api/v1/search``."""

    model_config = ConfigDict(str_strip_whitespace=True)

    criteria: dict[str, Any] = Field(
        default_factory=dict,
        description="Echo of applied query parameters (type, location, minPrice, …).",
    )
    results: list[Properties]
    total: int
    limit: int
    offset: int
