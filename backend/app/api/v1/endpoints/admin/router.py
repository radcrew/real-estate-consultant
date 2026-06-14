"""Admin-only management endpoints."""

from __future__ import annotations

import logging
from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.db_safe import execute_db_safe
from app.core.deps import CurrentAdmin, SupabaseSdkDep
from app.services.ingestion_client import wake_processor

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)


class IngestRequest(BaseModel):
    source: str = "loopnet-seed"


class EnqueueResponse(BaseModel):
    job_id: str
    source: str
    status: str
    idempotency_key: str


@router.post("/ingest", response_model=EnqueueResponse, summary="Enqueue an ingestion job")
async def enqueue_ingest(
    _admin: CurrentAdmin,
    body: IngestRequest,
    client: SupabaseSdkDep,
) -> EnqueueResponse:
    """Insert a pending job into the queue; returns immediately with job_id.

    A GitHub Actions poller calls the ingestion service every 15 minutes,
    which calls claim_next_job() to atomically pick it up.
    """
    source = body.source
    idem_key = f"{source}:{date.today().isoformat()}"

    existing = await execute_db_safe(
        client.table("jobs")
        .select("id,status")
        .eq("idempotency_key", idem_key)
        .in_("status", ["pending", "running"])
        .limit(1)
        .execute()
    )
    if existing.data:
        row = existing.data[0]
        raise HTTPException(
            status_code=409,
            detail=f"Job for {source!r} is already {row['status']!r} today.",
        )

    result = await execute_db_safe(
        client.table("jobs").insert({"source": source, "idempotency_key": idem_key}).execute()
    )
    job = result.data[0]
    logger.info("job_enqueued", extra={"job_id": job["id"], "source": source, "idem_key": idem_key})
    await wake_processor()
    return EnqueueResponse(
        job_id=job["id"],
        source=source,
        status="pending",
        idempotency_key=idem_key,
    )
