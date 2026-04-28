"""Pydantic shapes for Hugging Face intake JSON (aligned with ``public.questions``)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, RootModel, ValidationInfo, field_validator


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
    is_complete: bool = False

    @field_validator("extracted", mode="before")
    @classmethod
    def _coerce_extracted(cls, v: object) -> dict[str, Any]:
        if isinstance(v, dict):
            return dict(v)
        return {}

    @field_validator("extracted", mode="after")
    @classmethod
    def _strip_unknown_criteria_keys(
        cls,
        v: dict[str, Any],
        info: ValidationInfo,
    ) -> dict[str, Any]:
        ctx = info.context or {}
        allowed = ctx.get("allowed_criteria_keys")
        if not isinstance(allowed, (set, frozenset, list, tuple)):
            return v
        allow = set(allowed)
        return {k: val for k, val in v.items() if k in allow}


class LlmExtractedIntakePayload(RootModel[dict[str, Any]]):
    """Sparse criteria extracted from user text; keys match ``public.questions.key``."""
