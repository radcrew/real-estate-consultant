"""HTTP client for the ingestion microservice."""

from __future__ import annotations

import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(connect=5.0, read=30.0, write=5.0, pool=5.0)


async def wake_processor() -> None:
    """Best-effort call to process the job queue immediately.

    If this fails (service down, auth not configured yet), the job stays
    queued and is picked up by the ingestion service's Vercel cron within
    15 minutes, so failures here are logged and swallowed.
    """
    if not settings.ingestion_service_url:
        return

    url = settings.ingestion_service_url.rstrip("/") + "/api/v1/jobs/process"
    headers = {"Authorization": f"Bearer {settings.ingestion_service_token}"}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(url, headers=headers)
            resp.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("ingestion_wake_failed", extra={"error": str(exc)})
