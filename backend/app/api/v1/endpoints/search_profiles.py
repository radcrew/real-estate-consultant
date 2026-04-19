"""``public.search_profiles`` (Supabase)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.core.db_safe import execute_db_safe
from app.core.deps import CurrentUser, SupabaseSdkDep
from app.models.search_profiles import SearchProfile
from app.schemas.search_profiles import CreateSearchProfileRequest

router = APIRouter(tags=["search-profiles"])


def _expect_one_row(raw: object, *, detail: str) -> dict:
    if isinstance(raw, list):
        if len(raw) != 1:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)
        row = raw[0]
    elif isinstance(raw, dict):
        row = raw
    else:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)
    if not isinstance(row, dict):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)
    return row


@router.post(
    "/search-profiles",
    status_code=status.HTTP_201_CREATED,
    response_model=SearchProfile,
)
async def create_search_profile(
    body: CreateSearchProfileRequest,
    client: SupabaseSdkDep,
    current_user: CurrentUser,
) -> SearchProfile:
    payload: dict[str, object] = {"user_id": str(current_user.id)}
    if body.name is not None:
        payload["name"] = body.name
    result = await execute_db_safe(client.table("search_profiles").insert(payload).execute())
    row = _expect_one_row(
        result.data,
        detail="Unexpected response from Supabase when creating search profile.",
    )
    return SearchProfile.model_validate(row)
