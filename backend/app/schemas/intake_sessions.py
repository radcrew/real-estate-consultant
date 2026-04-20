"""API payloads for ``public.intake_sessions``."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateIntakeSessionRequest(BaseModel):
    """Request body for ``POST /api/v1/intake-sessions``.

    If ``search_profile_id`` is omitted, a new ``search_profiles`` row is created for the
    authenticated user and linked to this session.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    status: str = Field(default="in_progress")
    search_profile_id: UUID | None = None
    criteria: Any | None = None


class PatchIntakeSessionStatusRequest(BaseModel):
    """Request body for ``PATCH /api/v1/intake-sessions/{session_id}`` (status only)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    status: str
