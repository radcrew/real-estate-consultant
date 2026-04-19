"""API payloads for ``public.intake_sessions``."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateIntakeSessionRequest(BaseModel):
    """Request body for ``POST /api/v1/intake-sessions``."""

    model_config = ConfigDict(str_strip_whitespace=True)

    status: str = Field(default="in_progress")
    search_profile_id: UUID | None = None
    criteria: Any | None = None
