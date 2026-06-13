"""HTTP client for the ingestion microservice."""

from __future__ import annotations

import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# Long read timeout: connector runs can take tens of seconds for large datasets.
_TIMEOUT = httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=5.0)


async def trigger_ingest(source: str = "loopnet-seed") -> dict:
    """POST /api/v1/ingest on the ingestion service and return the JSON response."""
    base = settings.ingestion_service_url.rstrip("/")
    url = f"{base}/api/v1/ingest"
    logger.info("ingestion_client_call", extra={"url": url, "source": source})
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(url, json={"source": source})
        resp.raise_for_status()
        return resp.json()
