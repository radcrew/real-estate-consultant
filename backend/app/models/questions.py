"""Row shape for the ``public.questions`` table (questionnaire flow)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class Question(BaseModel):
    """Question definition (matches ``public.questions``)."""

    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)

    id: UUID | None = None
    question_text: str = Field(alias="text")
    question_type: str = Field(default="text", alias="type")
    order_index: int
    created_at: AwareDatetime | None = None
    required: bool = False
    options: Any | None = None
    key: str
