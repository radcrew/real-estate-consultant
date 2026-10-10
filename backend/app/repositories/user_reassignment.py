"""Move everything one user owns onto another user, in one transaction.

Used when a Google-only user is folded into an email/password user: the Google user is
about to be deleted from Cognito, so its data must move to the account that remains.

Both sides are resolved to the id their rows are really keyed by: the Supabase ``uuid``
for users moved over from Supabase Auth (a ``cognito_identity_mapping`` row), else the
``sub`` itself. Mapping rows are left alone, so the destination keeps resolving as before.

Where the destination already owns a matching row, its row wins:

- ``profiles``: the destination's empty columns are filled from the source row.
- Any primary or unique key that includes the user column: source rows that would
  collide with a destination row are dropped. The keys are read from the catalog, since
  several of these tables were created outside the migrations folder.
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

# Profile columns a user fills in; the destination keeps its own value when it has one.
_PROFILE_FILL_COLUMNS: tuple[str, ...] = (
    "email",
    "phone",
    "first_name",
    "last_name",
    "address",
    "zip_code",
    "country",
    "city",
    "state",
    "avatar_url",
)

_RESOLVE_SQL = text(
    "select coalesce("
    "(select uuid::text from public.cognito_identity_mapping where sub = cast(:sub as text)), "
    "cast(:sub as text))"
)

_UNIQUE_KEYS_SQL = text(
    "select array_agg(a.attname::text order by a.attnum) "
    "from pg_constraint c "
    "join pg_attribute a on a.attrelid = c.conrelid and a.attnum = any(c.conkey) "
    "where c.conrelid = cast(cast(:table as text) as regclass) and c.contype in ('p', 'u') "
    "group by c.oid"
)


async def _resolve(session: AsyncSession, sub: str) -> str:
    return str((await session.execute(_RESOLVE_SQL, {"sub": sub})).scalar_one())


async def reassign_user(session: AsyncSession, old_sub: str, new_sub: str) -> None:
    """Move ``old_sub``'s data onto ``new_sub``'s account. Raises ``SQLAlchemyError``."""
    async with session.begin():
        old_id = await _resolve(session, old_sub)
        new_id = await _resolve(session, new_sub)
        if old_id == new_id:
            return
        params = {"old": old_id, "new": new_id}

        fills = ", ".join(f"{c} = coalesce(d.{c}, s.{c})" for c in _PROFILE_FILL_COLUMNS)
        await session.execute(
            text(
                f"update public.profiles d set {fills} from public.profiles s "
                "where d.id = cast(:new as uuid) and s.id = cast(:old as uuid)"
            ),
            params,
        )

        for table, column in _USER_ID_COLUMNS:
            keys = await session.execute(_UNIQUE_KEYS_SQL, {"table": f"public.{table}"})
            for (key_columns,) in keys.all():
                if column not in key_columns:
                    continue
                same = "".join(
                    f' and d."{c}" is not distinct from s."{c}"'
                    for c in key_columns
                    if c != column
                )
                await session.execute(
                    text(
                        f'delete from public.{table} s where s."{column}" = cast(:old as uuid) '
                        f'and exists (select 1 from public.{table} d '
                        f'where d."{column}" = cast(:new as uuid){same})'
                    ),
                    params,
                )
            await session.execute(
                text(
                    f'update public.{table} set "{column}" = cast(:new as uuid) '
                    f'where "{column}" = cast(:old as uuid)'
                ),
                params,
            )
