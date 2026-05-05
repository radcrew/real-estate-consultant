"""Property search (``public.properties``)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, DbSession, SupabaseSdkDep
from app.models.properties import Properties
from app.repositories.intake_sessions import load_intake_session_row_by_search_profile_id
from app.repositories.properties_search import search_properties
from app.repositories.search_profiles import ensure_search_profile_access
from app.schemas.search import PropertyMatch, SearchPropertiesResponse

router = APIRouter(tags=["search"])


@router.get(
    "/search/{session_profile_id}",
    response_model=SearchPropertiesResponse,
    summary="Search properties for a session profile",
)
async def search_listings(
    session_profile_id: UUID,
    client: SupabaseSdkDep,
    db: DbSession,
    current_user: CurrentUser,
    limit: int = Query(20, ge=1, le=100, description="Page size (max 100)."),
    offset: int = Query(0, ge=0, description="Offset for pagination."),
) -> SearchPropertiesResponse:
    """``GET /api/v1/search/{session_profile_id}?limit=50&offset=0``

    Resolves ``criteria`` from ``intake_sessions`` for this ``search_profile_id`` (most recent row).
    """
    await ensure_search_profile_access(
        client,
        session_profile_id,
        current_user.id,
    )
    session_row = await load_intake_session_row_by_search_profile_id(client, session_profile_id)
    raw_criteria = session_row.get("criteria")
    criteria: dict[str, Any] = dict(raw_criteria) if isinstance(raw_criteria, dict) else {}

    rows_with_scores, total = await search_properties(client, criteria, limit=limit, offset=offset)
    results = [
        PropertyMatch(property=Properties.model_validate(row), match_score=score)
        for row, score in rows_with_scores
    ]
    return SearchPropertiesResponse(
        criteria=criteria,
        results=results,
        total=total,
        limit=limit,
        offset=offset,
    )
