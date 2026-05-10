"""Authenticated account profile and password endpoints (Supabase Auth + ``public.profiles``)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status

from app.core.deps import CurrentUser, SupabaseSdkDep
from app.models.profile import profile_from_row
from app.repositories.account import apply_account_profile_patch
from app.repositories.profiles import (
    fetch_profile_row,
)
from app.schemas.account import (
    AccountPasswordChangeRequest,
    AccountProfileResponse,
    AccountProfileUpdate,
)
from app.utils.account_profile import account_profile_response
from app.utils.supabase.admin_user import admin_get_user, admin_update_user_password
from app.utils.supabase.password_verify import verify_current_email_password

router = APIRouter(prefix="/account", tags=["account"])


@router.get("/profile", response_model=AccountProfileResponse)
async def get_account_profile(
    current_user: CurrentUser,
    client: SupabaseSdkDep,
) -> AccountProfileResponse:
    user_id = UUID(current_user.id)

    auth_user = await admin_get_user(client, current_user.id)
    raw = await fetch_profile_row(client, user_id)
    return account_profile_response(user=auth_user, profile=profile_from_row(raw))


@router.patch("/profile", response_model=AccountProfileResponse)
async def patch_account_profile(
    body: AccountProfileUpdate,
    current_user: CurrentUser,
    client: SupabaseSdkDep,
) -> AccountProfileResponse:
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update.",
        )

    user_id = UUID(current_user.id)
    return await apply_account_profile_patch(
        client,
        user_id=user_id,
        supabase_user_id=current_user.id,
        body=body,
        updates=updates,
    )


@router.post("/password", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def change_account_password(
    body: AccountPasswordChangeRequest,
    current_user: CurrentUser,
    client: SupabaseSdkDep,
) -> Response:
    email = (current_user.email or "").strip()
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account has no email; password change is not supported here.",
        )

    await verify_current_email_password(email=email, password=body.current_password)

    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="New password must be different from your current password.",
        )

    await admin_update_user_password(client, current_user.id, new_password=body.new_password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
