"""Tests for the migration runner's pure parts.

Applying SQL needs a database; ordering, discovery and URL handling do not — and those
are where a mistake is silent rather than loud.
"""
from __future__ import annotations

from scripts.migrate import (
    MIGRATIONS_DIR,
    asyncpg_url,
    checksum,
    discover_migrations,
    uses_pgbouncer,
)


class TestAsyncpgUrl:
    def test_strips_the_sqlalchemy_driver_suffix(self):
        assert (
            asyncpg_url("postgresql+asyncpg://u:p@host:5432/db")
            == "postgresql://u:p@host:5432/db"
        )

    def test_leaves_a_plain_url_alone(self):
        url = "postgresql://u:p@host:5432/db"
        assert asyncpg_url(url) == url


class TestPgbouncerGuard:
    def test_detects_the_pooled_port(self):
        """Transaction mode rejects DDL, so this would fail mid-run without the check."""
        assert uses_pgbouncer("postgresql://u:p@db.example.supabase.co:6543/postgres")

    def test_direct_port_is_fine(self):
        assert not uses_pgbouncer("postgresql://u:p@db.example.supabase.co:5432/postgres")


class TestDiscovery:
    def test_finds_the_repository_migrations(self):
        """Guard the guard: an empty result would make the ordering test vacuous."""
        found = discover_migrations()
        assert len(found) >= 3
        assert all(path.suffix == ".sql" for path in found)

    def test_orders_by_filename(self):
        """Load-bearing: 20260815 alters a policy that 20260814 creates, so lexical
        order has to be apply order."""
        names = [path.name for path in discover_migrations()]
        assert names == sorted(names)
        assert names.index("20260814_intake_jobs.sql") < names.index(
            "20260815_intake_sessions_user_id.sql"
        )

    def test_names_are_unique(self):
        """The tracking table keys on filename, so a duplicate would silently skip one."""
        names = [path.name for path in discover_migrations()]
        assert len(names) == len(set(names))

    def test_points_at_the_repository_directory(self):
        assert MIGRATIONS_DIR.is_dir()
        assert MIGRATIONS_DIR.name == "migrations"


class TestChecksum:
    def test_is_stable_for_the_same_content(self, tmp_path):
        path = tmp_path / "0001_x.sql"
        path.write_text("select 1;", encoding="utf-8")
        assert checksum(path) == checksum(path)

    def test_changes_when_the_file_changes(self, tmp_path):
        """This is what catches an already-applied migration being edited — the way two
        environments quietly end up with different schemas."""
        path = tmp_path / "0001_x.sql"
        path.write_text("select 1;", encoding="utf-8")
        before = checksum(path)
        path.write_text("select 2;", encoding="utf-8")
        assert checksum(path) != before
