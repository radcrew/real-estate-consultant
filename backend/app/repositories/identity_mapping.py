"""``public.cognito_identity_mapping``: Cognito ``sub`` to the app's user id.

Users moved over from Supabase Auth keep their old Supabase ``uuid``, which every table
references, and get a row here. Users created in Cognito afterwards have no row; their
``sub`` is their user id.
"""

from __future__ import annotations

from app.core.db_safe import execute_db_safe
from app.utils.supabase.response import as_row_list
from supabase import AsyncClient


async def resolve_user_id(client: AsyncClient, sub: str) -> str:
    """The user id that keys this user's rows: the mapped ``uuid``, else the ``sub``."""
    result = await execute_db_safe(
        client.table("cognito_identity_mapping")
        .select("uuid")
        .eq("sub", sub)
        .limit(1)
        .execute(),
    )
    rows = as_row_list(result.data)
    return str(rows[0]["uuid"]) if rows else sub
