"""Public endpoint returning daily-rotating featured listings."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.deps import DbSession, SupabaseSdkDep
from app.models.properties import Properties
from app.repositories.featured import get_featured_property_rows
from app.repositories.property_images import fetch_first_image_url
from app.schemas.listings import ListingDetailResponse
from app.utils.listings import format_listing_type_label

router = APIRouter()


class FeaturedListingsResponse(BaseModel):
    listings: list[ListingDetailResponse]


@router.get(
    "/listings/featured",
    response_model=FeaturedListingsResponse,
    summary="Featured listings",
    tags=["listings"],
)
async def get_featured_listings(
    db: DbSession,
    client: SupabaseSdkDep,
) -> FeaturedListingsResponse:
    rows = await get_featured_property_rows(db)

    listings: list[ListingDetailResponse] = []
    for row in rows:
        image = await fetch_first_image_url(client, row["id"])
        payload = {**row, "image": image}
        payload["listing_type"] = format_listing_type_label(row.get("listing_type"))
        prop = Properties.model_validate(payload)
        listings.append(ListingDetailResponse(property=prop, images=[image] if image else []))

    return FeaturedListingsResponse(listings=listings)
