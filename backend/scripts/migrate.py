"""Apply the SQL migrations in ``supabase/migrations`` in order, once each.

Run from ``backend/``::

    python scripts/migrate.py --dry-run   # what would run
    python scripts/migrate.py             # apply it

**Why not Alembic.** Only ``properties`` has a SQLAlchemy model; every other table is
reached through PostgREST. Alembic's autogenerate diffs models against the database, so
with most tables unmodelled it would propose dropping them — a destructive default on a
live schema. And these migrations are RLS policies, triggers, extensions and column
comments, none of which autogenerate produces: they would end up as ``op.execute("...")``
wrapping this same SQL, paying the ceremony for none of the benefit.

So this stays raw SQL, and all this adds is *ordering*, *once-only*, and a record of what
ran. The Supabase CLI remains a fine alternative for branching and diffing; it reads the
same files.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
from pathlib import Path

import asyncpg

from app.core.config import settings

MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "supabase" / "migrations"

CREATE_TRACKING_TABLE = """
create table if not exists public.schema_migrations (
  filename text primary key,
  checksum text not null,
  applied_at timestamptz not null default now()
)
"""


def asyncpg_url(database_url: str) -> str:
    """asyncpg wants a plain URL; the app's may carry SQLAlchemy's driver suffix."""
    return database_url.replace("postgresql+asyncpg://", "postgresql://", 1)


def discover_migrations(directory: Path = MIGRATIONS_DIR) -> list[Path]:
    """Migration files in filename order.

    The names are date-prefixed, so lexical order is apply order — which is load-bearing:
    ``20260815`` alters a policy that ``20260814`` creates.
    """
    return sorted(directory.glob("*.sql"))


def checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def uses_pgbouncer(database_url: str) -> bool:
    """Supabase's pooled port. Transaction mode rejects DDL, so migrations need 5432."""
    return ":6543/" in database_url


async def run(*, dry_run: bool) -> int:
    if uses_pgbouncer(settings.database_url):
        print(
            "DATABASE_URL points at port 6543 (pgbouncer). Transaction mode blocks DDL —\n"
            "use the direct port 5432 for migrations."
        )
        return 1

    migrations = discover_migrations()
    if not migrations:
        print(f"No migrations found in {MIGRATIONS_DIR}")
        return 0

    conn = await asyncpg.connect(asyncpg_url(settings.database_url))
    try:
        await conn.execute(CREATE_TRACKING_TABLE)
        applied = {
            row["filename"]: row["checksum"]
            for row in await conn.fetch("select filename, checksum from public.schema_migrations")
        }

        # An edited migration that already ran is how two environments quietly diverge:
        # this database has the old version, the next one to migrate gets the new.
        for path in migrations:
            if path.name in applied and applied[path.name] != checksum(path):
                print(f"CHANGED SINCE APPLIED: {path.name} — write a new migration instead")

        pending = [path for path in migrations if path.name not in applied]
        if not pending:
            print(f"Up to date — {len(applied)} migration(s) already applied.")
            return 0

        print(f"Pending ({len(pending)}):")
        for path in pending:
            print(f"  {path.name}")
        if dry_run:
            return 0

        for path in pending:
            print(f"Applying {path.name} ...", end=" ", flush=True)
            # One transaction per migration: a failure leaves the ones before it applied
            # and recorded, so a re-run resumes rather than starting over.
            async with conn.transaction():
                await conn.execute(path.read_text(encoding="utf-8"))
                await conn.execute(
                    "insert into public.schema_migrations (filename, checksum) values ($1, $2)",
                    path.name,
                    checksum(path),
                )
            print("ok")
        print(f"Applied {len(pending)} migration(s).")
        return 0
    finally:
        await conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List what would be applied without running it.",
    )
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run(dry_run=args.dry_run)))


if __name__ == "__main__":
    main()
