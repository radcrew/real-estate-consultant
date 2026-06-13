"""Pydantic shapes for structured LLM intake outputs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


class LlmParseNextQuestion(BaseModel):
    """LLM-authored pointer to the next questionnaire step."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    key: str | None = None
    text: str | None = None

    @field_validator("key", "text", mode="before")
    @classmethod
    def validate_optional_text(cls, value: object) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return None


class LlmOpeningQuestionOutput(BaseModel):
    """Structured opening-question payload from the provider."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    text: str = ""

    @field_validator("text", mode="before")
    @classmethod
    def validate_text(cls, value: object) -> str:
        if isinstance(value, str):
            return value.strip()
        return ""

class LlmParseModelOutput(BaseModel):
    """Expected top-level JSON object from the intake parsing model."""

    model_config = ConfigDict(extra="ignore")

    extracted: dict[str, Any] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    skipped_fields: list[str] = Field(default_factory=list)
    next_question: LlmParseNextQuestion = Field(default_factory=LlmParseNextQuestion)
    is_complete: bool = False

    @field_validator("extracted", mode="before")
    @classmethod
    def validate_extracted(cls, v: object, info: ValidationInfo) -> dict[str, Any]:
        if not isinstance(v, dict):
            return {}

        data = dict(v)

        allowed = info.context.get("allowed_criteria_keys") if info.context else None
        if isinstance(allowed, (set, list, tuple, frozenset)):
            allowed_set = set(allowed)
            data = {k: val for k, val in data.items() if k in allowed_set}

        return data

    @field_validator("missing_fields", "skipped_fields", mode="before")
    @classmethod
    def validate_missing_fields(cls, value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, str)]

    @field_validator("next_question", mode="before")
    @classmethod
    def validate_next_question(cls, value: object) -> dict[str, object]:
        if isinstance(value, dict):
            return value
        return {}

    @field_validator("is_complete", mode="before")
    @classmethod
    def validate_is_complete(cls, value: object) -> bool:
        if isinstance(value, bool):
            return value
        return False
