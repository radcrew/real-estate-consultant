"""POST /api/v1/ingest — trigger a connector run synchronously."""

from __future__ import annotations

import logging
import time

from fastapi import APIRouter, HTTPException
from supabase import acreate_client

from app.connectors.loopnet_seed import LoopNetSeedConnector
from app.core.config import settings
from app.schemas.ingest import IngestRequest, IngestResponse

router = APIRouter(prefix="/ingest", tags=["ingest"])
logger = logging.getLogger(__name__)

_CONNECTORS = {
    "loopnet-seed": LoopNetSeedConnector,
}


@router.post("", response_model=IngestResponse)
async def trigger_ingest(body: IngestRequest) -> IngestResponse:
    connector_cls = _CONNECTORS.get(body.source)
    if connector_cls is None:
        raise HTTPException(status_code=400, detail=f"Unknown source: {body.source!r}")

    client = await acreate_client(settings.supabase_url, settings.supabase_service_role_key)
    connector = connector_cls(client)
    start = time.perf_counter()
    try:
        report = await connector.run()
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        await client.postgrest.aclose()

    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    return IngestResponse(
        source=report.source,
        fetched=report.fetched,
        normalized=report.normalized,
        rejected=report.rejected,
        rejected_reasons=report.rejected_reasons,
        duration_ms=duration_ms,
    )
