"""Property search (``public.properties``)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, DbSession, SupabaseSdkDep
from app.models.properties import Properties
from app.repositories.intake_sessions import (
    load_intake_session_row_by_search_profile_id,
    parse_intake_session,
    save_intake_criteria,
)
from app.repositories.properties_search import search_properties
from app.repositories.questions import load_question_key_metadata
from app.repositories.search_profiles import ensure_search_profile_access
from app.schemas.search import (
    PropertyMatch,
    SearchCriteriaUpdateResponse,
    SearchPropertiesResponse,
    UpdateSearchCriteriaBody,
)
from app.utils.search_criteria import normalize_criteria

router = APIRouter(tags=["search"])


@router.get(
    "/search/{session_profile_id}",
    response_model=SearchPropertiesResponse,
    response_model_exclude_none=True,
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

    key_types, key_titles = await load_question_key_metadata(client)
    criteria_with_types = normalize_criteria(criteria, key_types, key_titles)

    rows_with_scores, total = await search_properties(db, criteria, limit=limit, offset=offset)
    results = [
        PropertyMatch(property=Properties.model_validate(row), match_score=score)
        for row, score in rows_with_scores
    ]
    return SearchPropertiesResponse(
        criteria=criteria_with_types,
        results=results,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.put(
    "/search/{session_profile_id}",
    response_model=SearchCriteriaUpdateResponse,
    response_model_exclude_none=True,
    summary="Replace search criteria on the linked intake session",
)
async def update_search_criteria(
    session_profile_id: UUID,
    client: SupabaseSdkDep,
    current_user: CurrentUser,
    body: UpdateSearchCriteriaBody,
) -> SearchCriteriaUpdateResponse:
    """``PUT /api/v1/search/{session_profile_id}``

    Replaces ``criteria`` on the **latest** ``intake_sessions`` row for this search profile.
    Body shape matches the merged object from guided answers (multiple keys at once).
    """
    await ensure_search_profile_access(
        client,
        session_profile_id,
        current_user.id,
    )
    session_row = await load_intake_session_row_by_search_profile_id(client, session_profile_id)
    criteria = dict(body.root)
    updated = await save_intake_criteria(client, UUID(str(session_row["id"])), criteria)
    session = parse_intake_session(updated)
    raw_after = session.criteria
    criteria_dict: dict[str, Any] = dict(raw_after) if isinstance(raw_after, dict) else {}

    key_types, key_titles = await load_question_key_metadata(client)
    criteria_wrapped = normalize_criteria(criteria_dict, key_types, key_titles)

    return SearchCriteriaUpdateResponse(
        id=session.id,
        status=session.status,
        created_at=session.created_at,
        search_profile_id=session.search_profile_id,
        criteria=criteria_wrapped,
    )
