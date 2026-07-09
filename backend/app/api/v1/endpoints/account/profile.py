from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter

from app.api.v1.endpoints.account.exceptions import (
    raise_account_no_fields_to_update,
)
from app.core.deps import CurrentUser, SupabaseSdkDep
from app.models.profile import profile_from_row
from app.repositories.account import (
    get_auth_user,
    update_auth_user,
)
from app.repositories.profiles import (
    PROFILE_PATCH_DB_COLUMNS,
    get_profile_row,
    upsert_profile_patch,
)
from app.schemas.account import (
    AccountProfileResponse,
    AccountProfileUpdate,
)
from app.utils.account_profile import account_profile_response

router = APIRouter()


@router.get("/profile", response_model=AccountProfileResponse)
async def get_account_profile(
    current_user: CurrentUser,
    client: SupabaseSdkDep,
) -> AccountProfileResponse:
    user_id = UUID(current_user.id)

    user = await get_auth_user(client, current_user.id)
    raw = await get_profile_row(client, user_id)
    return account_profile_response(user=user, profile=profile_from_row(raw))


@router.patch("/profile", response_model=AccountProfileResponse)
async def update_account_profile(
    body: AccountProfileUpdate,
    current_user: CurrentUser,
    client: SupabaseSdkDep,
) -> AccountProfileResponse:
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise_account_no_fields_to_update()

    user_id = UUID(current_user.id)

    auth_user_updates: dict[str, Any] = {}
    if "email" in updates:
        auth_user_updates["email"] = str(updates["email"])
    if "phone" in updates:
        auth_user_updates["phone"] = updates["phone"]

    has_profile_updates = bool(set(updates) & PROFILE_PATCH_DB_COLUMNS)
    if has_profile_updates:
        await upsert_profile_patch(client, user_id, body)
    if auth_user_updates:
        await update_auth_user(client, current_user.id, auth_user_updates)

    user = await get_auth_user(client, current_user.id)
    raw = await get_profile_row(client, user_id)
    return account_profile_response(user=user, profile=profile_from_row(raw))
