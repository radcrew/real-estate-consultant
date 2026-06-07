"""Public 'list your property' submissions (unauthenticated)."""

from __future__ import annotations

from fastapi import APIRouter, status

from app.core.deps import SupabaseSdkDep
from app.repositories.listing_submissions import create_listing_submission
from app.schemas.listings import ListingSubmissionCreate, ListingSubmissionResponse

router = APIRouter(prefix="/listing-submissions", tags=["submissions"])


@router.post(
    "",
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
