"""Property search (``public.properties``)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Query

from app.core.deps import CurrentUser, DbSession, SupabaseSdkDep
from app.models.properties import Properties
from app.repositories.intake_sessions import (
    load_profile_session_row,
    parse_intake_session,
    save_intake_criteria,
)
from app.repositories.properties import normalize_criteria, search_properties
from app.repositories.property_images import fetch_first_image_url
from app.repositories.search_profiles import ensure_search_profile_access
from app.schemas.search import (
    PropertyMatch,
    SearchCriteriaUpdateResponse,
    SearchPropertiesResponse,
    UpdateSearchCriteriaBody,
)
from app.utils.listings import format_listing_type_label

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
    await ensure_search_profile_access(
        client,
        session_profile_id,
        current_user.id,
    )

    session_row = await load_profile_session_row(client, session_profile_id)
    raw_criteria = session_row.get("criteria")
    criteria: dict[str, Any] = dict(raw_criteria) if isinstance(raw_criteria, dict) else {}

    rows_with_scores, total = await search_properties(db, criteria, limit=limit, offset=offset)
    results: list[PropertyMatch] = []
    for row, score in rows_with_scores:
        property_id = row["id"]
        image_url = await fetch_first_image_url(client, property_id)
        payload = {**row, "image": image_url}
        payload["listing_type"] = format_listing_type_label(row.get("listing_type"))
        results.append(
            PropertyMatch(
                property=Properties.model_validate(payload),
                match_score=score,
            ),
        )

    normalized_criteria = await normalize_criteria(client, criteria)

    return SearchPropertiesResponse(
        criteria=normalized_criteria,
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
    await ensure_search_profile_access(
        client,
        session_profile_id,
        current_user.id,
    )

    session_row = await load_profile_session_row(client, session_profile_id)
    criteria = dict(body.root)
    updated_session_row = await save_intake_criteria(client, UUID(str(session_row["id"])), criteria)
    session = parse_intake_session(updated_session_row)

    normalized_criteria = await normalize_criteria(client, criteria)

    return SearchCriteriaUpdateResponse(
        id=session.id,
        status=session.status,
        created_at=session.created_at,
        search_profile_id=session.search_profile_id,
        criteria=normalized_criteria,
    )
