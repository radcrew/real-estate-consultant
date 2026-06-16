"""HTTP client for the ingestion microservice."""

from __future__ import annotations

import logging

import httpx

from app.clients.ingestion.client import IngestionClient
from app.core.config import settings

logger = logging.getLogger(__name__)


async def wake_processor() -> None:
    """Best-effort call to process the job queue immediately.

    If this fails (service down, auth not configured yet), the job stays
    queued and is picked up by the GitHub Actions job poller within 15
    minutes, so failures here are logged and swallowed.
    """
    if not settings.ingestion_service_url:
        return

    client = IngestionClient(settings.ingestion_service_url, settings.ingestion_service_token)
    try:
        result = await client.process_jobs()
        logger.info(
            "ingestion_wake_processed",
            extra={
                "processed": result.processed,
                "job_id": result.job_id,
                "status": result.status,
            },
        )
    except httpx.HTTPError as exc:
        logger.warning("ingestion_wake_failed", extra={"error": str(exc)})
