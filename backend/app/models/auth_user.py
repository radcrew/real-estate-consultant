"""The authenticated caller, independent of which identity provider issued the credential."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AuthUser:
    """``id`` keys every table: the user's Supabase ``uuid`` from
    ``cognito_identity_mapping`` if they have one, otherwise their Cognito ``sub``.

    ``username`` is Cognito's user name, set only for access-token callers (``google_…``
    for Google users). MCP API key callers have none. Auth never loads the profile, so
    ``email`` and ``phone`` are unset here; account routes read them from the profile row.
    """

    id: str
    email: str | None = None
    phone: str | None = None
    username: str | None = None
