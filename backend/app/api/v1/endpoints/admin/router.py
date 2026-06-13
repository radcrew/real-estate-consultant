"""Admin-only management endpoints."""

from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.core.deps import CurrentAdmin
from app.services import ingestion_client

router = APIRouter(prefix="/admin", tags=["admin"])

logger = logging.getLogger(__name__)


class IngestRequest(BaseModel):
    source: str = "loopnet-seed"


@router.post("/ingest", summary="Trigger a connector run on the ingestion service")
async def trigger_ingest(_admin: CurrentAdmin, body: IngestRequest) -> dict:
    if not settings.ingestion_service_url:
        raise HTTPException(
            status_code=503,
            detail="INGESTION_SERVICE_URL is not configured.",
        )
    try:
        return await ingestion_client.trigger_ingest(body.source)
    except httpx.HTTPStatusError as exc:
        logger.error(
            "ingestion_service_error",
            extra={"status": exc.response.status_code, "body": exc.response.text},
        )
        raise HTTPException(status_code=502, detail="Ingestion service returned an error.") from exc
    except httpx.HTTPError as exc:
        logger.error("ingestion_service_unreachable", extra={"error": str(exc)})
        raise HTTPException(status_code=502, detail="Ingestion service is unreachable.") from exc
