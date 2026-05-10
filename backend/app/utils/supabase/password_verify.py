"""Verify a user's current password using the Supabase anon client (password grant)."""

from __future__ import annotations

import logging

import httpx
from fastapi import HTTPException, status
from supabase import AuthApiError, AuthInvalidCredentialsError, acreate_client
from supabase.lib.client_options import AsyncClientOptions

from app.core.config import settings

logger = logging.getLogger(__name__)

_SUPABASE_HTTP_TIMEOUT = httpx.Timeout(connect=30.0, read=120.0, write=30.0, pool=15.0)


async def verify_current_email_password(*, email: str, password: str) -> None:
    """
    Confirm ``password`` matches the account for ``email`` via ``sign_in_with_password``.

    Requires ``SUPABASE_ANON_KEY``; uses a short-lived client per call.
    """
    anon = settings.supabase_anon_key.strip()
    if not anon:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Password change is not configured (set SUPABASE_ANON_KEY on the API).",
        )

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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect.",
        ) from exc
    except AuthApiError as exc:
        if exc.code in ("invalid_credentials", "invalid_grant"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect.",
            ) from exc
        logger.warning("Supabase auth error while verifying password: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not verify password. Try again later.",
        ) from exc
    except httpx.HTTPError as exc:
        logger.warning("HTTP error while verifying password: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is temporarily unavailable.",
        ) from exc
    finally:
        await http.aclose()
