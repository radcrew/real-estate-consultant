"""API payloads for questionnaire questions."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CreateQuestionRequest(BaseModel):
    """Request body for ``POST /api/v1/questions``."""

    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)

    text: str
    question_type: str = Field(
        default="text",
        alias="type",
        description="Question control type (e.g. text, single_choice).",
    )
    order_index: int
    required: bool = False
    options: Any | None = None
    key: str
