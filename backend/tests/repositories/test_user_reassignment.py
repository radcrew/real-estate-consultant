"""Moving a user's rows onto another user's account."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from app.repositories.user_reassignment import reassign_user

_OLD = "11111111-1111-4111-8111-111111111111"
_NEW = "22222222-2222-4222-8222-222222222222"
_MAPPED = "33333333-3333-4333-8333-333333333333"

# Unique keys per table, as the catalog would answer.
_KEYS = {
    "public.profiles": [(["id"],)],
    "public.saved_listings": [(["user_id", "property_id"],)],
    "public.mcp_api_keys": [(["id"],)],
}


def _session(mapping: dict[str, str] | None = None) -> MagicMock:
    """A fake session: resolves subs through ``mapping`` and answers key lookups."""
    mapping = mapping or {}
    session = MagicMock()
    begin = MagicMock()
    begin.__aenter__ = AsyncMock(return_value=None)
    begin.__aexit__ = AsyncMock(return_value=False)
    session.begin.return_value = begin

    async def execute(statement, params=None):
        sql = str(statement)
        if "cognito_identity_mapping" in sql:
            return SimpleNamespace(scalar_one=lambda: mapping.get(params["sub"], params["sub"]))
        if "pg_constraint" in sql:
            return SimpleNamespace(all=lambda: _KEYS.get(params["table"], []))
        return SimpleNamespace(rowcount=0)

    session.execute = AsyncMock(side_effect=execute)
    return session


def _writes(session) -> list[tuple[str, dict]]:
    """Statements that change data, with their parameters."""
    return [
        (str(call.args[0]), call.args[1])
        for call in session.execute.await_args_list
        if str(call.args[0]).startswith(("update", "delete"))
    ]


class TestReassignUser:
    async def test_moves_every_user_table_to_the_new_id(self):
        session = _session()
        await reassign_user(session, _OLD, _NEW)
        # The move itself, not the profile gap fill ("update public.profiles d set ...").
        moves = [sql for sql, _ in _writes(session) if ' set "' in sql]
        assert [sql.split()[1] for sql in moves] == [
            "public.profiles",
            "public.favorites",
            "public.intake_sessions",
            "public.mcp_api_keys",
            "public.outreach_drafts",
            "public.saved_listings",
            "public.search_profiles",
        ]
        assert all(params == {"old": _OLD, "new": _NEW} for _, params in _writes(session))

    async def test_mapped_destination_receives_rows_under_its_supabase_uuid(self):
        """Requests resolve a migrated user's sub to their uuid; rows must land there."""
        session = _session(mapping={_NEW: _MAPPED})
        await reassign_user(session, _OLD, _NEW)
        assert all(params == {"old": _OLD, "new": _MAPPED} for _, params in _writes(session))

    async def test_mapped_source_moves_rows_from_its_supabase_uuid(self):
        session = _session(mapping={_OLD: _MAPPED})
        await reassign_user(session, _OLD, _NEW)
        assert all(params == {"old": _MAPPED, "new": _NEW} for _, params in _writes(session))

    async def test_destination_profile_keeps_its_values_and_fills_gaps(self):
        session = _session()
        await reassign_user(session, _OLD, _NEW)
        fill = _writes(session)[0][0]
        assert fill.startswith("update public.profiles d set ")
        assert "first_name = coalesce(d.first_name, s.first_name)" in fill
        assert "phone = coalesce(d.phone, s.phone)" in fill

    async def test_colliding_rows_are_dropped_before_the_move(self):
        session = _session()
        await reassign_user(session, _OLD, _NEW)
        writes = [sql for sql, _ in _writes(session)]

        saved_delete = next(s for s in writes if s.startswith("delete from public.saved_listings"))
        assert 'd."property_id" is not distinct from s."property_id"' in saved_delete
        saved_move = next(s for s in writes if s.startswith("update public.saved_listings"))
        assert writes.index(saved_delete) < writes.index(saved_move)

        # A profile row is keyed by the user alone: the destination's row wins outright.
        profile_delete = next(s for s in writes if s.startswith("delete from public.profiles"))
        assert "is not distinct from" not in profile_delete

    async def test_keys_without_the_user_column_are_ignored(self):
        session = _session()
        await reassign_user(session, _OLD, _NEW)
        assert not any(s.startswith("delete from public.mcp_api_keys") for s, _ in _writes(session))

    async def test_same_account_on_both_sides_changes_nothing(self):
        session = _session(mapping={_OLD: _MAPPED, _NEW: _MAPPED})
        await reassign_user(session, _OLD, _NEW)
        assert _writes(session) == []

    async def test_runs_in_one_transaction(self):
        session = _session()
        await reassign_user(session, _OLD, _NEW)
        session.begin.assert_called_once()
