"""Single-listing read API (``public.properties`` + ``property_images``)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.core.deps import DbSession, SupabaseSdkDep
from app.models.properties import Properties
from app.repositories.property_images import fetch_all_image_urls
from app.repositories.properties import get_property_by_id
from app.schemas.listings import ListingDetailResponse

router = APIRouter(tags=["listings"])


@router.get(
    "/listings/{property_id}",
    response_model=ListingDetailResponse,
    response_model_exclude_none=True,
    summary="Listing detail",
)
async def get_listing_detail(
    property_id: UUID,
    client: SupabaseSdkDep,
    db: DbSession,
) -> ListingDetailResponse:
    row = await get_property_by_id(db, property_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found.")

    images = await fetch_all_image_urls(client, property_id)
    prop = Properties.model_validate({**row, "image": images[0] if images else None})

    return ListingDetailResponse(property=prop, images=images)
