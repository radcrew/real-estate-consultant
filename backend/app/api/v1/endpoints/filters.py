"""Filter catalog derived from ``questions`` (keys → type + label)."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.deps import SupabaseSdkDep
from app.repositories.questions import load_intake_question_filters
from app.schemas.filters import FilterResponse

router = APIRouter(tags=["filters"])


@router.get(
    "/filters",
    summary="List intake-driven filter definitions",
)
async def list_filters(
    client: SupabaseSdkDep,
) -> dict[str, FilterResponse]:
    """``GET /api/v1/filters``

    Keys match ``questions.key``; ``type`` and ``label`` map from ``questions.type``
    and ``questions.title``.
    """
    raw = await load_intake_question_filters(client)
    return {key: FilterResponse(**fields) for key, fields in raw.items()}
