"""Property search (``public.properties``)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter

from app.core.deps import SupabaseSdkDep
from app.models.properties import Properties
from app.repositories.properties_search import search_properties
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
) -> SearchPropertiesResponse:
    """``GET /api/v1/search/{session_profile_id}`` — path only; no query parameters."""
    criteria: dict[str, Any] = {"session_profile_id": str(session_profile_id)}
    limit = 50
    offset = 0
    rows, total = await search_properties(client, criteria, limit=limit, offset=offset)
    results = [
        PropertyMatch(property=Properties.model_validate(row), match_score=0.0) for row in rows
    ]
    return SearchPropertiesResponse(
        criteria=criteria,
        results=results,
        total=total,
        limit=limit,
        offset=offset,
    )
