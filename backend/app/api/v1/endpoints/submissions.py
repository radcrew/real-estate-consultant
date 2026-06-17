"""Listing submissions: public create + admin review."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.v1.endpoints.submission_images import router as submission_images_router
from app.core.deps import CurrentAdmin, SupabaseSdkDep, get_current_admin
from app.repositories.listing_submissions import (
    create_listing_submission,
    list_listing_submissions,
    update_submission_status,
)
from app.schemas.listings import (
    ListingSubmissionCreate,
    ListingSubmissionItem,
    ListingSubmissionResponse,
    ListingSubmissionStatusUpdate,
)
from app.utils.exceptions import raise_not_found

router = APIRouter(prefix="/listing-submissions", tags=["submissions"])
router.include_router(submission_images_router)


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


@router.get(
    "",
    response_model=list[ListingSubmissionItem],
    dependencies=[Depends(get_current_admin)],
    summary="List submissions (admin)",
)
async def list_submissions(client: SupabaseSdkDep) -> list[ListingSubmissionItem]:
    rows = await list_listing_submissions(client)
    return [ListingSubmissionItem.model_validate(row) for row in rows]


@router.patch(
    "/{submission_id}",
    response_model=ListingSubmissionItem,
    summary="Update a submission's status (admin)",
)
async def patch_submission(
    submission_id: str,
    body: ListingSubmissionStatusUpdate,
    _admin: CurrentAdmin,
    client: SupabaseSdkDep,
) -> ListingSubmissionItem:
    row = await update_submission_status(client, submission_id, body.status)
    if row is None:
        raise_not_found("Submission not found.")
    return ListingSubmissionItem.model_validate(row)
