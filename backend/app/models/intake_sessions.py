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
    criteria: Any | None = Field(
        default=None,
        description=(
            "Flat search criteria, e.g. location, property_type, min_size_sqft, max_price, "
            "min_clear_height, min_loading_docks."
        ),
    )
