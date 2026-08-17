"""The intake_jobs repository must only reference columns the migration creates.

Repository tests mock PostgREST, so they answer with whatever the fake returns — a column
that does not exist in the table passes every one of them and fails only against the real
database, on the first request after deploy.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.repositories import intake_jobs as repo

MIGRATION = (
    Path(__file__).resolve().parents[2]
    / "supabase"
    / "migrations"
    / "20260814_intake_jobs.sql"
)

# Columns the repository names outside the select list — filters and update payloads.
FILTERED_COLUMNS = {"id", "session_id", "status", "updated_at"}
WRITTEN_COLUMNS = {"session_id", "input", "status", "result", "error"}


# Table-constraint syntax, which also appears on continuation lines: a constraint spread
# over two lines puts `check (...)` at the start of the second one, where a naive parser
# reads it as a column.
_NOT_A_COLUMN = frozenset({"constraint", "check", "primary", "foreign", "unique", "exclude"})


def migration_columns() -> set[str]:
    """Column names from the ``create table`` block."""
    sql = MIGRATION.read_text(encoding="utf-8")
    block = re.search(
        r"create table if not exists public\.intake_jobs\s*\((.*?)\n\);",
        sql,
        re.DOTALL | re.IGNORECASE,
    )
    assert block, "could not find the create table block"

    columns: set[str] = set()
    for raw in block.group(1).splitlines():
        line = raw.strip()
        if not line or line.startswith("--"):
            continue
        name = re.match(r"([a-z_][a-z0-9_]*)\s+", line)
        if name and name.group(1).lower() not in _NOT_A_COLUMN:
            columns.add(name.group(1))
    return columns


def selected_columns() -> set[str]:
    return {part.strip() for part in repo._SELECT.split(",")}


class TestRepositoryMatchesMigration:
    def test_the_parser_finds_exactly_the_table_columns(self):
        """Guard the guard.

        A parse that finds nothing would make every assertion below vacuous, and one that
        over-matches — constraint keywords read as columns — would hide a real mismatch.
        """
        assert migration_columns() == {
            "id",
            "session_id",
            "status",
            "input",
            "result",
            "error",
            "attempts",
            "created_at",
            "updated_at",
            "started_at",
            "finished_at",
        }

    @pytest.mark.parametrize("column", sorted(selected_columns()))
    def test_every_selected_column_exists(self, column):
        assert column in migration_columns()

    @pytest.mark.parametrize("column", sorted(FILTERED_COLUMNS))
    def test_every_filtered_column_exists(self, column):
        assert column in migration_columns()

    @pytest.mark.parametrize("column", sorted(WRITTEN_COLUMNS))
    def test_every_written_column_exists(self, column):
        assert column in migration_columns()

    def test_attempts_is_never_written_by_the_repository(self):
        """It is trigger-maintained; a write here would race concurrent redelivery."""
        assert "attempts" not in WRITTEN_COLUMNS
        source = Path(repo.__file__).read_text(encoding="utf-8")
        assert '"attempts"' not in source

    def test_the_active_statuses_are_ones_the_check_constraint_allows(self):
        """A status outside the constraint would make every claim update fail."""
        sql = MIGRATION.read_text(encoding="utf-8")
        allowed = set(re.findall(r"'(queued|running|succeeded|failed)'", sql))
        assert set(repo.ACTIVE_STATUSES) <= allowed
