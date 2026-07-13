"""Fit explanation: explain why a property scored the way it did."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.api.v1.endpoints.listings.exceptions import raise_listing_not_found
from app.core.deps import CurrentUser, DbSession, SupabaseSdkDep
from app.llm.fit.service import generate_fit_explanation
from app.repositories.intake_sessions import get_profile_session_row
from app.repositories.properties import get_property_match_breakdown
from app.repositories.search_profiles import ensure_search_profile_access
from app.schemas.fit import FitExplanationResponse, FitScoreBreakdown

router = APIRouter(prefix="/search", tags=["search"])


@router.post(
    "/{session_profile_id}/fit/{property_id}",
    response_model=FitExplanationResponse,
    response_model_exclude_none=True,
    summary="Explain why a property matches the session's search criteria",
)
async def explain_fit(
    session_profile_id: UUID,
    property_id: UUID,
    client: SupabaseSdkDep,
    db: DbSession,
    current_user: CurrentUser,
) -> FitExplanationResponse:
    await ensure_search_profile_access(client, session_profile_id, current_user.id)

    session_row = await get_profile_session_row(client, session_profile_id)
    raw_criteria = session_row.get("criteria")
    criteria = dict(raw_criteria) if isinstance(raw_criteria, dict) else {}

    found = await get_property_match_breakdown(db, property_id, criteria)
    if found is None:
        raise_listing_not_found()
    property_row, (location_score, price_score, size_score, total_score) = found

    result = await generate_fit_explanation(
        criteria=criteria,
        property_row=property_row,
        location_score=location_score,
        price_score=price_score,
        size_score=size_score,
    )

    return FitExplanationResponse(
        property_id=property_id,
        score=FitScoreBreakdown(
            location=location_score,
            price=price_score,
            size=size_score,
            total=total_score,
        ),
        summary=result.summary,
        strengths=result.strengths,
        considerations=result.considerations,
    )
