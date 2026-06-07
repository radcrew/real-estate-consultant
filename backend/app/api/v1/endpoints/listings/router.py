"""Single-listing read API (``public.properties`` + ``property_images``)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from app.api.v1.endpoints.listings.exceptions import raise_listing_not_found
from app.core.deps import DbSession, SupabaseSdkDep
from app.models.properties import Properties
from app.repositories.listing_submissions import create_listing_submission
from app.repositories.properties import get_property_by_id
from app.repositories.property_images import fetch_all_image_urls
from app.schemas.listings import (
    ListingDetailResponse,
    ListingSubmissionCreate,
    ListingSubmissionResponse,
)
from app.utils.listings import format_listing_type_label

router = APIRouter(prefix="/listings", tags=["listings"])


@router.post(
    "/submissions",
    response_model=ListingSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a property listing (public)",
)
async def submit_listing(
    body: ListingSubmissionCreate,
    client: SupabaseSdkDep,
) -> ListingSubmissionResponse:
    row = await create_listing_submission(client, body.model_dump(mode="json"))
    return ListingSubmissionResponse(
        id=str(row.get("id", "")),
        status=str(row.get("status", "pending")),
    )


@router.get(
    "/{property_id}",
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
        raise_listing_not_found()

    images = await fetch_all_image_urls(client, property_id)
    payload = {**row, "image": images[0] if images else None}
    payload["listing_type"] = format_listing_type_label(row.get("listing_type"))
    prop = Properties.model_validate(payload)

    return ListingDetailResponse(property=prop, images=images)
