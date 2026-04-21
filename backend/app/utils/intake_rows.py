"""Row shaping for ``intake_sessions`` PostgREST responses."""

from __future__ import annotations

INTAKE_SESSION_EMBEDDED_RELATION_KEYS: frozenset[str] = frozenset({"search_profiles"})


def strip_intake_session_row(
    row: dict,
    *,
    extra_embedded_keys: frozenset[str] | None = None,
) -> dict:
    """Remove nested relation keys from a joined select (e.g. ``search_profiles``)."""
    excluded = INTAKE_SESSION_EMBEDDED_RELATION_KEYS | (extra_embedded_keys or frozenset())
    return {k: v for k, v in row.items() if k not in excluded}
