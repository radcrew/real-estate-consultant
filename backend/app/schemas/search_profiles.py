"""API payloads for ``public.search_profiles``."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CreateSearchProfileRequest(BaseModel):
    """Request body for ``POST /api/v1/search-profiles``."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, description="Optional label for this saved search.")
