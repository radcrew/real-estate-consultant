"""The authenticated caller, independent of which identity provider issued the credential."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AuthUser:
    """``id`` is the provider's user id (a UUID string) and keys ``public.profiles``."""

    id: str
    email: str | None = None
    phone: str | None = None


def auth_user_from_supabase(user: Any) -> AuthUser:
    """Adapt a ``supabase_auth.types.User`` while Supabase still issues tokens."""
    return AuthUser(id=user.id, email=user.email, phone=user.phone)
