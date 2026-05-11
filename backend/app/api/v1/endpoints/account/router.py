"""Authenticated account profile and password endpoints (Supabase Auth + ``public.profiles``)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Response, status

from app.core.deps import CurrentUser, SupabaseSdkDep
from app.exceptions.account_routes import (
    raise_account_new_password_same_as_current,
    raise_account_no_email_for_password_change,
    raise_account_no_fields_to_update,
)
from app.models.profile import profile_from_row
from app.repositories.account import (
    get_auth_user,
    update_auth_user,
    update_auth_user_password,
    verify_current_email_password,
)
from app.repositories.profiles import (
    PROFILE_PATCH_DB_COLUMNS,
    fetch_profile_row,
    upsert_profile_patch,
)
from app.schemas.account import (
    AccountPasswordChangeRequest,
    AccountProfileResponse,
    AccountProfileUpdate,
)
from app.utils.account_profile import account_profile_response

router = APIRouter(prefix="/account", tags=["account"])


@router.get("/profile", response_model=AccountProfileResponse)
async def get_account_profile(
    current_user: CurrentUser,
    client: SupabaseSdkDep,
) -> AccountProfileResponse:
    user_id = UUID(current_user.id)

    user = await get_auth_user(client, current_user.id)
    raw = await fetch_profile_row(client, user_id)
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
    raw = await fetch_profile_row(client, user_id)
    return account_profile_response(user=user, profile=profile_from_row(raw))


@router.post("/password", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def change_account_password(
    body: AccountPasswordChangeRequest,
    current_user: CurrentUser,
    client: SupabaseSdkDep,
) -> Response:
    email = (current_user.email or "").strip()
    if not email:
        raise_account_no_email_for_password_change()

    await verify_current_email_password(client, email=email, password=body.current_password)

    if body.current_password == body.new_password:
        raise_account_new_password_same_as_current()

    await update_auth_user_password(client, current_user.id, new_password=body.new_password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
