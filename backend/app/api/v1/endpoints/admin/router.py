"""Admin-only management endpoints."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.v1.endpoints.admin.exceptions import raise_job_already_queued, raise_job_not_found
from app.core.deps import CurrentAdmin, SupabaseSdkDep
from app.repositories.jobs import (
    get_active_job_by_idempotency_key,
    get_job_row,
    insert_job_row,
)
from app.services.ingestion import wake_processor

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)


class IngestRequest(BaseModel):
    source: str = "loopnet-seed"


class EnqueueResponse(BaseModel):
    job_id: str
    source: str
    status: str
    idempotency_key: str


class JobResponse(BaseModel):
    id: str
    source: str
    status: str
    attempts: int
    result: dict[str, Any] | None = None
    error: str | None = None


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

    existing = await get_active_job_by_idempotency_key(client, idem_key)
    if existing is not None:
        raise_job_already_queued(source, existing["status"])

    job = await insert_job_row(client, source=source, idempotency_key=idem_key)
    logger.info("job_enqueued", extra={"job_id": job["id"], "source": source, "idem_key": idem_key})
    await wake_processor()
    return EnqueueResponse(
        job_id=job["id"],
        source=source,
        status="pending",
        idempotency_key=idem_key,
    )


@router.get("/jobs/{job_id}", response_model=JobResponse, summary="Get an ingestion job")
async def get_job(
    _admin: CurrentAdmin,
    job_id: UUID,
    client: SupabaseSdkDep,
) -> JobResponse:
    """Polled by the admin page while a job runs; replaces the browser's Realtime feed."""
    row = await get_job_row(client, job_id)
    if row is None:
        raise_job_not_found()
    return JobResponse.model_validate(row)
