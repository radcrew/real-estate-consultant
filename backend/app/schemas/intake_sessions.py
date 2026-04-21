"""API payloads for ``public.intake_sessions``."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.intake_sessions import IntakeSession


class IntakeSessionFirstQuestion(BaseModel):
    """Minimal first-question payload returned when starting intake."""

    key: str
    text: str
    type: str


class CreateIntakeSessionResponse(BaseModel):
    """Response body for ``POST /api/v1/intake-sessions``."""

    model_config = ConfigDict(str_strip_whitespace=True)

    session_id: UUID
    status: str
    first_question: IntakeSessionFirstQuestion


class PatchIntakeSessionStatusRequest(BaseModel):
    """Request body for ``PATCH /api/v1/intake-sessions/{session_id}`` (status only)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    status: str


class SubmitIntakeSessionAnswersRequest(BaseModel):
    """Request body for ``PATCH /api/v1/intake-sessions/{session_id}/answers``."""

    model_config = ConfigDict(str_strip_whitespace=True)

    answers: Any = Field(
        ...,
        description=(
            "Partial criteria object (e.g. ``location``, ``property_type``, ``min_size_sqft``), "
            "shallow-merged into session ``criteria``."
        ),
    )
    key: str | None = Field(
        default=None,
        description="Question ``key`` for this step (should match a criteria field name such as ``location``).",
    )


class SubmitIntakeSessionAnswersResponse(BaseModel):
    """Response for ``PATCH /api/v1/intake-sessions/{session_id}/answers``."""

    model_config = ConfigDict(str_strip_whitespace=True)

    session: IntakeSession
    next_question: IntakeSessionFirstQuestion | None = None
