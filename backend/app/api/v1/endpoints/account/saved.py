"""Per-user saved listings for the authenticated account."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from app.core.deps import CurrentUser, SupabaseSdkDep
from app.repositories.saved_listings import (
    add_saved_listing,
    list_saved_property_ids,
    remove_saved_listing,
)
from app.schemas.account import SavedListingCreate, SavedListingsResponse

router = APIRouter()


@router.get("/saved", response_model=SavedListingsResponse)
async def get_saved_listings(
    current_user: CurrentUser,
    client: SupabaseSdkDep,
) -> SavedListingsResponse:
    ids = await list_saved_property_ids(client, UUID(current_user.id))
    return SavedListingsResponse(property_ids=ids)


@router.post("/saved", status_code=status.HTTP_204_NO_CONTENT)
async def save_listing(
    body: SavedListingCreate,
    current_user: CurrentUser,
    client: SupabaseSdkDep,
) -> None:
    await add_saved_listing(client, UUID(current_user.id), body.property_id)


@router.delete("/saved/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unsave_listing(
    property_id: str,
    current_user: CurrentUser,
    client: SupabaseSdkDep,
) -> None:
    await remove_saved_listing(client, UUID(current_user.id), property_id)
