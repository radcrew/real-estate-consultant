"""``public.questions`` (Supabase)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.core.db_safe import execute_db_safe
from app.core.deps import SupabaseSdkDep
from app.models.questions import Question
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
    result = await execute_db_safe(client.table("questions").insert(payload).execute())

    raw = result.data
    if isinstance(raw, list):
        if len(raw) != 1:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unexpected response from Supabase when creating question.",
            )
        row = raw[0]
    elif isinstance(raw, dict):
        row = raw
    else:
        row = None

    if not isinstance(row, dict):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected response from Supabase when creating question.",
        )
    return Question.model_validate(row)
