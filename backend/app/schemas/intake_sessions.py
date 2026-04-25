"""API payloads for ``public.intake_sessions``."""

from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.intake_sessions import IntakeSession


class IntakeSessionFirstQuestion(BaseModel):
    """Minimal first-question payload returned when starting intake."""

    key: str
    text: str
    type: str


class CreateIntakeSessionResponseGuided(BaseModel):
    """Guided flow: first questionnaire step is returned."""

    model_config = ConfigDict(str_strip_whitespace=True)

    mode: Literal["guided"] = "guided"
    session_id: UUID
    status: str
    first_question: IntakeSessionFirstQuestion


class CreateIntakeSessionResponseLlm(BaseModel):
    """LLM flow: client receives an open-ended prompt; session is still created for follow-up APIs."""

    model_config = ConfigDict(str_strip_whitespace=True)

    mode: Literal["llm"] = "llm"
    session_id: UUID
    status: str
    message: str


CreateIntakeSessionResponse = (
    CreateIntakeSessionResponseGuided | CreateIntakeSessionResponseLlm
)


class PatchIntakeSessionStatusRequest(BaseModel):
    """Request body for ``PATCH /api/v1/intake-sessions/{session_id}`` (status only)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    status: str


class UpdateIntakeSessionAnswersRequest(BaseModel):
    """Request body for ``PATCH /api/v1/intake-sessions/{session_id}/answers``."""

    model_config = ConfigDict(str_strip_whitespace=True)

    key: str = Field(
        ...,
        description="Criteria field name for this step (e.g. ``location``, ``property_type``).",
    )
    answers: Any = Field(
        ...,
        description="Value stored at ``criteria[key]`` (string, number, or structured object).",
    )


class UpdateIntakeSessionAnswersResponse(BaseModel):
    """Response for ``PATCH /api/v1/intake-sessions/{session_id}/answers``."""

    model_config = ConfigDict(str_strip_whitespace=True)

    session: IntakeSession
    next_question: IntakeSessionFirstQuestion | None = None


class SubmitLlmIntakeInputRequest(BaseModel):
    """Request body for ``POST /api/v1/intake-sessions/{session_id}/llm-input``."""

    model_config = ConfigDict(str_strip_whitespace=True)

    input: str = Field(..., description="User free-text intake prompt.")


class LlmExtractedLocation(BaseModel):
    label: str
    lat: float | None = None
    lng: float | None = None


class LlmExtractedRange(BaseModel):
    min: float | None = None
    max: float | None = None


class LlmExtractedIntakePayload(BaseModel):
    building_type: list[str] | None = None
    location: LlmExtractedLocation | None = None
    size_sqft: LlmExtractedRange | None = None
    rent_range: LlmExtractedRange | None = None


class SubmitLlmIntakeInputResponse(BaseModel):
    """Response body for ``POST /api/v1/intake-sessions/{session_id}/llm-input``."""

    model_config = ConfigDict(str_strip_whitespace=True)

    extracted: LlmExtractedIntakePayload
    criteria: dict[str, Any]
    missing_fields: list[str]
    next_question: IntakeSessionFirstQuestion | None = None
    is_complete: bool
