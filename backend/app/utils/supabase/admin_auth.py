"""Map Supabase Auth API errors to FastAPI HTTP exceptions (admin / user update flows)."""

from __future__ import annotations

from fastapi import HTTPException, status
from supabase import AuthApiError


def http_exception_from_admin_auth_api_error(exc: AuthApiError) -> HTTPException:
    """Typical GoTrue errors when updating a user via the admin API."""
    if exc.code in ("email_exists", "user_already_exists", "phone_exists"):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That email or phone is already in use.",
        )
    if exc.code in ("email_not_confirmed", "provider_email_needs_verification"):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=exc.message,
        )
    status_code = exc.status if 400 <= exc.status < 600 else status.HTTP_400_BAD_REQUEST
    return HTTPException(status_code=status_code, detail=exc.message)
