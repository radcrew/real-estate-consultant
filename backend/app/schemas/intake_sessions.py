"""API payloads for ``public.intake_sessions``."""

from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.intake_sessions import IntakeSession


class IntakeSessionFirstQuestion(BaseModel):
    """Minimal first-question payload returned when starting intake."""

    key: str
    title: str
    text: str
    type: str
    options: Any | None = None


class CreateIntakeSessionGuidedResponse(BaseModel):
    """Guided flow: first questionnaire step is returned."""

    model_config = ConfigDict(str_strip_whitespace=True)

    mode: Literal["guided"] = "guided"
    session_id: UUID
    status: str
    current_index: int
    total_questions: int
    first_question: IntakeSessionFirstQuestion


class CreateIntakeSessionLlmResponse(BaseModel):
    """LLM flow: welcome plus an LLM-shaped next prompt (same shape as guided first question)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    mode: Literal["llm"] = "llm"
    session_id: UUID
    status: str
    current_index: int
    total_questions: int
    message: str
    next_question: IntakeSessionFirstQuestion


CreateIntakeSessionResponse = (
    CreateIntakeSessionGuidedResponse | CreateIntakeSessionLlmResponse
)


class GetIntakeSessionResponse(IntakeSession):
    """Stored intake session plus questionnaire position metadata."""

    current_index: int
    total_questions: int
    question_history: list[IntakeSessionFirstQuestion] = Field(default_factory=list)
    next_question: IntakeSessionFirstQuestion | None = None


class UpdateIntakeSessionAnswersRequest(BaseModel):
    """Request body for ``PATCH /api/v1/intake-sessions/{session_id}/answers/guided``."""

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
    """Response for ``PATCH /api/v1/intake-sessions/{session_id}/answers/guided``."""

    model_config = ConfigDict(str_strip_whitespace=True)

    session: IntakeSession
    current_index: int
    total_questions: int
    next_question: IntakeSessionFirstQuestion | None = None


class SubmitLlmIntakeInputRequest(BaseModel):
    """Request body for ``POST /api/v1/intake-sessions/{session_id}/answers/llm``."""

    model_config = ConfigDict(str_strip_whitespace=True)

    input: str = Field(..., description="User free-text intake prompt.")


class SubmitLlmIntakeInputResponse(BaseModel):
    """The turn's result. Delivered via the job, not the POST that started it."""

    model_config = ConfigDict(str_strip_whitespace=True)

    extracted: dict[str, Any]
    criteria: dict[str, Any]
    current_index: int
    total_questions: int
    missing_fields: list[str]
    # Answered in ``criteria`` but unsupported by anything the user said, so also present
    # in ``missing_fields``: a reading worth offering back and not worth trusting. Lets a
    # client say "I think industrial — is that right?" instead of asking from scratch.
    unconfirmed_fields: list[str] = []
    # Plain-language notes on what was done to the user's own words: a unit converted, a
    # figure that belongs to another field, a bound the wording moved. Empty for the
    # ordinary turn. Each is {field, kind, message}.
    notes: list[dict[str, str]] = []
    # Both were built by the service and passed here, but were never declared — Pydantic
    # dropped them silently, so the side panel's missing-field labels have always fallen
    # back to raw keys. Declared now, with defaults so an older stored job result still
    # loads.
    skipped_fields: list[str] = Field(default_factory=list)
    question_titles: dict[str, str] = Field(default_factory=dict)
    next_question: IntakeSessionFirstQuestion | None = None
    is_complete: bool


class EnqueuedLlmIntakeJobResponse(BaseModel):
    """``202`` body for ``POST /api/v1/intake-sessions/{session_id}/answers/llm``.

    Identical whether the turn was queued or run inline: the client always follows a job,
    so a deployment without a queue needs no different client code.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    job_id: UUID
    status: str = Field(description="queued | running | succeeded | failed")


class IntakeJobStatusResponse(BaseModel):
    """A job's current state, from the poll endpoint or an SSE frame."""

    model_config = ConfigDict(str_strip_whitespace=True)

    job_id: UUID
    status: str
    result: SubmitLlmIntakeInputResponse | None = None
    error: str | None = None
