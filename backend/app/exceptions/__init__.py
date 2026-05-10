"""Centralized HTTP error helpers (semantic ``raise_*`` functions)."""

from app.exceptions.supabase import (
    raise_could_not_load_profile,
    raise_current_password_incorrect,
    raise_password_auth_transport_unavailable,
    raise_password_change_not_configured,
    raise_password_verification_unavailable,
    raise_profile_service_unavailable,
    raise_weak_password,
)

__all__ = [
    "raise_could_not_load_profile",
    "raise_current_password_incorrect",
    "raise_password_auth_transport_unavailable",
    "raise_password_change_not_configured",
    "raise_password_verification_unavailable",
    "raise_profile_service_unavailable",
    "raise_weak_password",
]
