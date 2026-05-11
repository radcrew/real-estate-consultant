"""``public.questions`` (Supabase)."""

from __future__ import annotations

from fastapi import APIRouter, status

from app.core.deps import SupabaseSdkDep
from app.models.questions import Question
from app.repositories.questions import insert_question_row
from app.schemas.questions import CreateQuestionRequest

router = APIRouter(tags=["questions"])


@router.post(
    "/questions",
    status_code=status.HTTP_201_CREATED,
    response_model=Question,
    response_model_by_alias=True,
)
async def create_question(body: CreateQuestionRequest, client: SupabaseSdkDep) -> Question:
    payload = body.model_dump(mode="json", exclude_none=True, by_alias=True)
    row = await insert_question_row(client, payload)
    return Question.model_validate(row)
