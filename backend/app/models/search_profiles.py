"""Row shape for the ``public.search_profiles`` table."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, NaiveDatetime


class SearchProfile(BaseModel):
    """Saved search profile for a user (matches ``public.search_profiles``)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: UUID | None = None
    user_id: UUID | None = None
    name: str | None = None
    created_at: NaiveDatetime | None = None
