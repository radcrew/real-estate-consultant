"""POST /api/v1/jobs/process — claim and run the next pending job from the queue."""

from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from supabase import AsyncClient, acreate_client

from app.connectors.loopnet_seed import LoopNetSeedConnector
from app.core.auth import require_internal_token
from app.core.config import settings
from app.core.db_safe import execute_db_safe

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
    async with await acreate_client(settings.supabase_url, settings.supabase_service_role_key) as client:
        result = await execute_db_safe(client.rpc("claim_next_job").execute())
        if not result.data:
            return ProcessResponse(processed=False, message="No pending jobs.")

        job = result.data[0]
        job_id: str = job["id"]
        source: str = job["source"]
        attempts: int = job["attempts"]
        logger.info("job_claimed", extra={"job_id": job_id, "source": source, "attempt": attempts})

        connector_cls = _CONNECTORS.get(source)
        if connector_cls is None:
            await _update_job(client, job_id, "failed", error=f"Unknown source: {source!r}")
            return ProcessResponse(processed=True, job_id=job_id, source=source, status="failed")

        start = time.perf_counter()
        try:
            report = await connector_cls(client).run()
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            await _update_job(
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
            logger.info(
                "job_done",
                extra={"job_id": job_id, "source": source, "duration_ms": duration_ms},
            )
            return ProcessResponse(processed=True, job_id=job_id, source=source, status="done")

        except Exception as exc:
            logger.error("job_error", extra={"job_id": job_id, "source": source, "error": str(exc)})
            # Retry if under the attempt cap; otherwise fail permanently.
            retry_status = "pending" if attempts < _MAX_ATTEMPTS else "failed"
            await _update_job(client, job_id, retry_status, error=str(exc))
            return ProcessResponse(
                processed=True, job_id=job_id, source=source, status=retry_status
            )


async def _update_job(
    client: AsyncClient,
    job_id: str,
    status: str,
    *,
    result: dict | None = None,
    error: str | None = None,
) -> None:
    payload = {"status": status}
    if result is not None:
        payload["result"] = result
    if error is not None:
        payload["error"] = error
    await execute_db_safe(client.table("jobs").update(payload).eq("id", job_id).execute())
