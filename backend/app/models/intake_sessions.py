"""Row shape for the ``public.intake_sessions`` table."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class IntakeSession(BaseModel):
    """Intake flow session tied to a search profile (matches ``public.intake_sessions``)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: UUID | None = None
    status: str = Field(default="in_progress")
    created_at: AwareDatetime | None = None
    search_profile_id: UUID | None = None
    criteria: Any | None = None
