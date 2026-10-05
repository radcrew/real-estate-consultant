"""Moving a user's rows from an old Cognito sub to a new one."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from app.repositories.user_reassignment import reassign_user

_OLD = "11111111-1111-4111-8111-111111111111"
_NEW = "22222222-2222-4222-8222-222222222222"


def _session(mapping_rows: int) -> MagicMock:
    session = MagicMock()
    begin = MagicMock()
    begin.__aenter__ = AsyncMock(return_value=None)
    begin.__aexit__ = AsyncMock(return_value=False)
    session.begin.return_value = begin
    results = iter([SimpleNamespace(rowcount=mapping_rows)])
    session.execute = AsyncMock(
        side_effect=lambda *a, **k: next(results, SimpleNamespace(rowcount=0))
    )
    return session


def _sql(session) -> list[str]:
    return [str(call.args[0]) for call in session.execute.await_args_list]


class TestReassignUser:
    async def test_mapped_user_only_moves_the_mapping_row(self):
        session = _session(mapping_rows=1)
        assert await reassign_user(session, _OLD, _NEW) == "mapping"
        assert _sql(session) == [
            "update public.cognito_identity_mapping set sub = :new where sub = :old"
        ]
        assert session.execute.await_args.args[1] == {"old": _OLD, "new": _NEW}

    async def test_unmapped_user_rewrites_every_user_table(self):
        session = _session(mapping_rows=0)
        assert await reassign_user(session, _OLD, _NEW) == "tables"
        statements = _sql(session)[1:]
        assert [s.split()[1] for s in statements] == [
            "public.profiles",
            "public.favorites",
            "public.intake_sessions",
            "public.mcp_api_keys",
            "public.outreach_drafts",
            "public.saved_listings",
            "public.search_profiles",
        ]
        assert "set id = cast(:new as uuid) where id = cast(:old as uuid)" in statements[0]

    async def test_runs_in_one_transaction(self):
        session = _session(mapping_rows=0)
        await reassign_user(session, _OLD, _NEW)
        session.begin.assert_called_once()
