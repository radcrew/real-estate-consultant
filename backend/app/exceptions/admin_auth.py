"""Map Supabase Auth admin API errors to HTTP responses."""

from __future__ import annotations

from typing import NoReturn

from fastapi import status
from supabase import AuthApiError

from app.utils.exceptions import raise_client_error, raise_conflict, raise_forbidden


def raise_admin_auth_api_error(exc: AuthApiError) -> NoReturn:
    """Typical GoTrue errors when updating a user via the admin API."""
    if exc.code in ("email_exists", "user_already_exists", "phone_exists"):
        raise_conflict("That email or phone is already in use.", cause=exc)
    if exc.code in ("email_not_confirmed", "provider_email_needs_verification"):
        raise_forbidden(str(exc.message), cause=exc)
    status_code = exc.status if 400 <= exc.status < 600 else status.HTTP_400_BAD_REQUEST
    raise_client_error(status_code, str(exc.message), cause=exc)
