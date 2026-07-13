"""Shared Supabase fluent-query-builder mocks for direct repository tests."""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock

_CHAINABLE_METHODS = (
    "select",
    "eq",
    "neq",
    "in_",
    "order",
    "limit",
    "insert",
    "update",
    "upsert",
    "delete",
)


def make_table_mock(data: Any) -> MagicMock:
    """A fake PostgREST query builder: every chain method returns itself, and
    ``.execute()`` resolves to ``SimpleNamespace(data=data)``, regardless of chain length.
    """
    table = MagicMock()
    for name in _CHAINABLE_METHODS:
        getattr(table, name).return_value = table
    table.execute = AsyncMock(return_value=SimpleNamespace(data=data))
    return table


def make_supabase_client(data: Any = None) -> MagicMock:
    """A fake ``AsyncClient`` whose ``.table(...)`` always returns the same
    configured fluent mock (see ``make_table_mock``).
    """
    client = MagicMock()
    client.table.return_value = make_table_mock(data)
    return client
