"""Pydantic shapes for Hugging Face intake JSON (aligned with ``public.questions``)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


class LlmParseNextQuestion(BaseModel):
    """LLM-authored pointer to the next questionnaire step."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    key: str | None = None
    text: str | None = None

class LlmParseModelOutput(BaseModel):
    """Expected top-level JSON object from the intake parsing model."""

    model_config = ConfigDict(extra="ignore")

    extracted: dict[str, Any] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    next_question: LlmParseNextQuestion = Field(default_factory=LlmParseNextQuestion)
    i_complete: bool = False

    @field_validator("extracted", mode="before")
    @classmethod
    def validate_extracted(cls, v: object, info: ValidationInfo) -> dict[str, Any]:
        # Coerce to dict
        if not isinstance(v, dict):
            return {}

        data = dict(v)

        # Filter by allowed keys if provided
        allowed = info.context.get("allowed_criteria_keys") if info.context else None
        if isinstance(allowed, (set, list, tuple, frozenset)):
            allowed_set = set(allowed)
            data = {k: val for k, val in data.items() if k in allowed_set}

        return data