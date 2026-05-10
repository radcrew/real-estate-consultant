"""Orchestrate account profile reads and patches (Auth admin + ``public.profiles``)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from supabase import AsyncClient

from app.models.profile import profile_from_row
from app.repositories.profiles import (
    PROFILE_PATCH_DB_COLUMNS,
    fetch_profile_row,
    upsert_profile_patch,
)
from app.schemas.account import AccountProfileResponse, AccountProfileUpdate
from app.utils.supabase.admin_user import admin_get_user, admin_update_user
from app.utils.account_profile import account_profile_response

async def apply_account_profile_patch(
    client: AsyncClient,
    *,
    user_id: UUID,
    supabase_user_id: str,
    body: AccountProfileUpdate,
    updates: dict[str, Any],
) -> AccountProfileResponse:
    touches_profiles_table = bool(set(updates) & PROFILE_PATCH_DB_COLUMNS)
    auth_attrs: dict[str, Any] = {}
    if "email" in updates:
        auth_attrs["email"] = str(updates["email"])
    if "phone" in updates:
        auth_attrs["phone"] = updates["phone"]

    if touches_profiles_table:
        await upsert_profile_patch(client, user_id, body)
    if auth_attrs:
        await admin_update_user(client, supabase_user_id, auth_attrs)

    auth_user = await admin_get_user(client, supabase_user_id)
    raw = await fetch_profile_row(client, user_id)
    return account_profile_response(user=auth_user, profile=profile_from_row(raw))
