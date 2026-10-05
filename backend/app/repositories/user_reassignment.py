"""Move everything a user owns from one Cognito ``sub`` to another, in one transaction.

Used when a Google-only user is merged into a new email/password user: the Google user is
deleted from Cognito, so its ``sub`` must stop being the key for its data.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Every public column that holds an app user id. Keep in step with new user-keyed tables.
_USER_ID_COLUMNS: tuple[tuple[str, str], ...] = (
    ("profiles", "id"),
    ("favorites", "user_id"),
    ("intake_sessions", "user_id"),
    ("mcp_api_keys", "user_id"),
    ("outreach_drafts", "user_id"),
    ("saved_listings", "user_id"),
    ("search_profiles", "user_id"),
)


async def reassign_user(session: AsyncSession, old_sub: str, new_sub: str) -> str:
    """Point ``old_sub``'s data at ``new_sub``. Returns which path was taken.

    A user moved over from Supabase Auth has a ``cognito_identity_mapping`` row, and their
    tables hold the Supabase ``uuid``; moving that row to the new ``sub`` is enough
    ("mapping"). Otherwise the tables hold the ``sub`` itself and are rewritten ("tables").
    """
    params = {"old": old_sub, "new": new_sub}
    async with session.begin():
        moved = await session.execute(
            text("update public.cognito_identity_mapping set sub = :new where sub = :old"),
            params,
        )
        if moved.rowcount:
            return "mapping"
        for table, column in _USER_ID_COLUMNS:
            await session.execute(
                text(
                    f"update public.{table} set {column} = cast(:new as uuid) "
                    f"where {column} = cast(:old as uuid)"
                ),
                params,
            )
    return "tables"
