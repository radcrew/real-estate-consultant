"""Load and update ``public.profiles`` via Supabase (PostgREST)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from supabase import AsyncClient

from app.core.db_safe import execute_db_safe
from app.schemas.account import AccountProfileUpdate
from app.utils.exceptions import raise_bad_gateway
from app.utils.supabase.response import as_row_list

PROFILE_PATCH_DB_COLUMNS: frozenset[str] = frozenset(
    {
        "first_name",
        "last_name",
        "address",
        "zip_code",
        "country",
        "city",
        "state",
        "email",
    },
)

_PROFILE_SELECT = ",".join(
    (
        "id",
        "email",
        "created_at",
        "is_admin",
        "first_name",
        "last_name",
        "address",
        "zip_code",
        "country",
        "city",
        "state",
        "avatar_url",
    ),
)
_LOAD_PROFILE_ERROR = "Unexpected response from Supabase when loading profile."


async def get_profile_row(client: AsyncClient, user_id: UUID) -> dict[str, Any] | None:
    result = await execute_db_safe(
        client.table("profiles")
        .select(_PROFILE_SELECT)
        .eq("id", str(user_id))
        .limit(1)
        .execute(),
    )
    rows = as_row_list(result.data)
    if not rows:
        return None
    row = rows[0]
    if not isinstance(row, dict):
        raise_bad_gateway(_LOAD_PROFILE_ERROR)
    return row


def _profile_patch_dict(body: AccountProfileUpdate) -> dict[str, Any]:
    data = body.model_dump(exclude_unset=True)
    return {k: v for k, v in data.items() if k in PROFILE_PATCH_DB_COLUMNS}


async def upsert_profile_patch(
    client: AsyncClient,
    user_id: UUID,
    body: AccountProfileUpdate,
) -> None:
    """Insert or update ``public.profiles`` columns present in the patch (not ``phone``)."""
    patch = _profile_patch_dict(body)
    if not patch:
        return

    existing = await get_profile_row(client, user_id)
    if existing is None:
        insert_row: dict[str, Any] = {"id": str(user_id), **patch}
        await execute_db_safe(client.table("profiles").insert(insert_row).execute())
        return

    await execute_db_safe(
        client.table("profiles").update(patch).eq("id", str(user_id)).execute(),
    )


async def set_profile_avatar_url(
    client: AsyncClient,
    user_id: UUID,
    avatar_url: str,
) -> None:
    """Insert or update only the ``avatar_url`` column for a profile."""
    existing = await get_profile_row(client, user_id)
    if existing is None:
        await execute_db_safe(
            client.table("profiles")
            .insert({"id": str(user_id), "avatar_url": avatar_url})
            .execute(),
        )
        return

    await execute_db_safe(
        client.table("profiles")
        .update({"avatar_url": avatar_url})
        .eq("id", str(user_id))
        .execute(),
    )
