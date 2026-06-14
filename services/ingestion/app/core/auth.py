"""Shared-secret bearer auth for service-to-service and cron calls.

Rotation: set SERVICE_AUTH_TOKEN_NEXT to the new value and deploy (both
tokens accepted), update the backend's INGESTION_SERVICE_TOKEN to the new
value and deploy, then promote SERVICE_AUTH_TOKEN_NEXT to SERVICE_AUTH_TOKEN
and clear SERVICE_AUTH_TOKEN_NEXT.
"""

from __future__ import annotations

from fastapi import HTTPException, Request

from app.core.config import settings


def _bearer_token(request: Request) -> str:
    auth = request.headers.get("authorization", "")
    scheme, _, token = auth.partition(" ")
    return token if scheme.lower() == "bearer" else ""


def require_service_token(request: Request) -> None:
    """Require Authorization: Bearer <SERVICE_AUTH_TOKEN[_NEXT]>.

    For endpoints only the backend should call directly.
    """
    valid = {t for t in (settings.service_auth_token, settings.service_auth_token_next) if t}
    if not valid:
        raise HTTPException(status_code=503, detail="Service auth not configured.")
    if _bearer_token(request) not in valid:
        raise HTTPException(status_code=401, detail="Unauthorized")


def require_internal_token(request: Request) -> None:
    """Require the cron secret (Vercel cron) or the service token (backend).

    For endpoints called by both internal callers.
    """
    valid = {
        t
        for t in (
            settings.cron_secret,
            settings.service_auth_token,
            settings.service_auth_token_next,
        )
        if t
    }
    if not valid:
        raise HTTPException(status_code=503, detail="Internal auth not configured.")
    if _bearer_token(request) not in valid:
        raise HTTPException(status_code=401, detail="Unauthorized")
