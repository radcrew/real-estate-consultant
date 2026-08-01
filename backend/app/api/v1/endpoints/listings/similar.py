"""Public endpoint: similar listings via embedding cosine similarity."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query

from app.api.v1.endpoints.listings.exceptions import raise_listing_not_found
from app.core.deps import DbSession, SupabaseSdkDep
from app.domain.listings import format_listing_type_label
from app.models.properties import Properties
from app.repositories.property_images import get_first_image_url
from app.schemas.listings import SimilarListingMatch, SimilarListingsResponse
from app.services.similar_listings import find_similar_listings

router = APIRouter()


@router.get(
    "/listings/{property_id}/similar",
    response_model=SimilarListingsResponse,
    response_model_exclude_none=True,
    summary="Similar listings",
    tags=["listings"],
)
async def get_similar_listings(
    property_id: UUID,
    client: SupabaseSdkDep,
    db: DbSession,
    limit: int = Query(6, ge=1, le=20, description="Max similar listings to return."),
) -> SimilarListingsResponse:
    ranked = await find_similar_listings(db, property_id, limit=limit)
    if ranked is None:
        raise_listing_not_found()

    results: list[SimilarListingMatch] = []
    for row, score in ranked:
        image = await get_first_image_url(client, row["id"])
        payload = {**row, "image": image}
        payload["listing_type"] = format_listing_type_label(row.get("listing_type"))
        results.append(
            SimilarListingMatch(
                property=Properties.model_validate(payload),
                match_score=score,
            )
        )

    return SimilarListingsResponse(results=results, limit=limit)
