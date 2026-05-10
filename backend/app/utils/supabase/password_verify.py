"""Verify a user's current password using the Supabase anon client (password grant)."""

from __future__ import annotations

import logging

import httpx
from supabase import AuthApiError, AuthInvalidCredentialsError, acreate_client
from supabase.lib.client_options import AsyncClientOptions

from app.core.config import settings
from app.exceptions.supabase import (
    raise_current_password_incorrect,
    raise_password_auth_transport_unavailable,
    raise_password_change_not_configured,
    raise_password_verification_unavailable,
)

logger = logging.getLogger(__name__)

_SUPABASE_HTTP_TIMEOUT = httpx.Timeout(connect=30.0, read=120.0, write=30.0, pool=15.0)


async def verify_current_email_password(*, email: str, password: str) -> None:
    """
    Confirm ``password`` matches the account for ``email`` via ``sign_in_with_password``.

    Requires ``SUPABASE_ANON_KEY``; uses a short-lived client per call.
    """
    anon = settings.supabase_anon_key.strip()
    if not anon:
        raise_password_change_not_configured()

    http = httpx.AsyncClient(
        timeout=_SUPABASE_HTTP_TIMEOUT,
        follow_redirects=True,
        http2=True,
    )
    try:
        client = await acreate_client(
            settings.supabase_url,
            anon,
            options=AsyncClientOptions(httpx_client=http),
        )
        await client.auth.sign_in_with_password({"email": email, "password": password})
    except AuthInvalidCredentialsError as exc:
        raise_current_password_incorrect(cause=exc)
    except AuthApiError as exc:
        if exc.code in ("invalid_credentials", "invalid_grant"):
            raise_current_password_incorrect(cause=exc)
        logger.warning("Supabase auth error while verifying password: %s", exc)
        raise_password_verification_unavailable(cause=exc)
    except httpx.HTTPError as exc:
        logger.warning("HTTP error while verifying password: %s", exc)
        raise_password_auth_transport_unavailable(cause=exc)
    finally:
        await http.aclose()
