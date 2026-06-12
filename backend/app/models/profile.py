"""Row shape for ``public.profiles`` (Supabase / PostgREST)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, NaiveDatetime


class Profile(BaseModel):
    """User profile row keyed by ``auth.users`` id."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: UUID
    email: str | None = None
    created_at: NaiveDatetime | None = None
    is_admin: bool | None = None
    first_name: str | None = None
    last_name: str | None = None
    address: str | None = None
    zip_code: str | None = None
    country: str | None = None
    city: str | None = None
    state: str | None = None
    avatar_url: str | None = None


def profile_from_row(row: dict[str, Any] | None) -> Profile | None:
    if row is None:
        return None
    return Profile.model_validate(row)
