"""API payloads for ``public.intake_sessions``."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CreateIntakeSessionRequest(BaseModel):
    """Request body for ``POST /api/v1/intake-sessions``."""

    model_config = ConfigDict(str_strip_whitespace=True)

    status: str = Field(default="in_progress")
    criteria: Any | None = None


class PatchIntakeSessionStatusRequest(BaseModel):
    """Request body for ``PATCH /api/v1/intake-sessions/{session_id}`` (status only)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    status: str
