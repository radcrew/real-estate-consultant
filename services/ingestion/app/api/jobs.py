"""POST /api/v1/jobs/process — claim and run the next pending job from the queue."""

from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel
from supabase import AsyncClient, acreate_client

from app.connectors.base import ConnectorBase
from app.connectors.loopnet_seed import LoopNetSeedConnector
from app.core.auth import require_internal_token
from app.core.config import settings
from app.repositories.jobs import claim_next_job, insert_job_row, update_job_status

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
    dependencies=[Depends(require_internal_token)],
)
logger = logging.getLogger(__name__)

_MAX_ATTEMPTS = 3

_CONNECTORS = {
    "loopnet-seed": LoopNetSeedConnector,
}


class ProcessResponse(BaseModel):
    processed: bool
    job_id: str | None = None
    source: str | None = None
    status: str | None = None
    message: str | None = None


@router.post("/process", response_model=ProcessResponse)
async def process_next_job() -> ProcessResponse:
    """Claim one pending job, run its connector, and update status to done/failed.

    Called by the GitHub Actions job poller every 15 minutes, or by the backend
    to process the queue immediately after enqueueing (see require_internal_token).
    """
    async with await acreate_client(
            settings.supabase_url,
            settings.supabase_service_role_key,
        ) as client:

        job = await claim_next_job(client)
        if job is None:
            return ProcessResponse(processed=False, message="No pending jobs.")

        job_id: str = job["id"]
        source: str = job["source"]
        attempts: int = job["attempts"]
        logger.info("job_claimed", extra={"job_id": job_id, "source": source, "attempt": attempts})

        connector_cls = _CONNECTORS.get(source)
        if connector_cls is None:
            await update_job_status(client, job_id, "failed", error=f"Unknown source: {source!r}")
            return ProcessResponse(processed=True, job_id=job_id, source=source, status="failed")

        status = await _run_connector(client, job_id, source, attempts, connector_cls)
        return ProcessResponse(processed=True, job_id=job_id, source=source, status=status)


@router.post("/run/{source}", response_model=ProcessResponse)
async def run_job(
    source: str = Path(..., description="Connector source name, e.g. 'loopnet-seed'"),
) -> ProcessResponse:
    """Enqueue a job for `source` and immediately run it.

    Called by CI after the dataset file is updated (push to main).
    Reuses the same internal/cron token as /process.
    """
    if source not in _CONNECTORS:
        raise HTTPException(status_code=400, detail=f"Unknown source: {source!r}")

    async with await acreate_client(
            settings.supabase_url,
            settings.supabase_service_role_key,
        ) as client:

        job = await insert_job_row(client, source)
        job_id: str = job["id"]
        attempts: int = job.get("attempts", 0)
        logger.info("job_run_triggered", extra={"job_id": job_id, "source": source})

        status = await _run_connector(client, job_id, source, attempts, _CONNECTORS[source])
        return ProcessResponse(processed=True, job_id=job_id, source=source, status=status)


async def _run_connector(
    client: AsyncClient,
    job_id: str,
    source: str,
    attempts: int,
    connector_cls: type[ConnectorBase],
) -> str:
    start = time.perf_counter()
    try:
        report = await connector_cls(client).run()
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        await update_job_status(
            client,
            job_id,
            "done",
            result={
                "fetched": report.fetched,
                "normalized": report.normalized,
                "rejected": report.rejected,
                "rejected_reasons": report.rejected_reasons,
                "duration_ms": duration_ms,
            },
        )
        logger.info("job_done", extra={
            "job_id": job_id, 
            "source": source, 
            "duration_ms": duration_ms
            })
        return "done"
    except Exception as exc:
        logger.error("job_error", extra={"job_id": job_id, "source": source, "error": str(exc)})
        # Retry if under the attempt cap; otherwise fail permanently.
        retry_status = "pending" if attempts < _MAX_ATTEMPTS else "failed"
        await update_job_status(client, job_id, retry_status, error=str(exc))
        return retry_status
