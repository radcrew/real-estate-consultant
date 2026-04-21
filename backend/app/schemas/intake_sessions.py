"""API payloads for ``public.intake_sessions``."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.intake_sessions import IntakeSession


class IntakeSessionFirstQuestion(BaseModel):
    """Minimal first-question payload returned when starting intake."""

    id: UUID
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
        description="Answer fields keyed by question ``key``, shallow-merged into session ``criteria``.",
    )
    question_id: UUID | None = Field(
        default=None,
        description="Question row this step answers; used with ``order_index`` to choose the next question.",
    )


class SubmitIntakeSessionAnswersResponse(BaseModel):
    """Response for ``PATCH /api/v1/intake-sessions/{session_id}/answers``."""

    model_config = ConfigDict(str_strip_whitespace=True)

    session: IntakeSession
    next_question: IntakeSessionFirstQuestion | None = None
