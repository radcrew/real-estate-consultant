from datetime import UTC, datetime

import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import settings

router = APIRouter(tags=["system"])

_started_at: str = datetime.now(UTC).isoformat()


@router.api_route("/health/live", methods=["GET", "HEAD"])
def health_live() -> dict[str, str]:
    return {"status": "ok"}


@router.api_route("/health/ready", methods=["GET", "HEAD"])
async def health_ready() -> JSONResponse:
    key = settings.supabase_service_role_key
    supabase_ok = False
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(
                f"{settings.supabase_url}/rest/v1/",
                headers={"apikey": key},
            )
        supabase_ok = r.status_code < 500
    except Exception:
        supabase_ok = False

    body = {
        "status": "ok" if supabase_ok else "degraded",
        "checks": {"supabase": "ok" if supabase_ok else "fail"},
        "version": settings.version,
        "git_sha": settings.git_sha or "unknown",
        "started_at": _started_at,
    }
    return JSONResponse(content=body, status_code=200 if supabase_ok else 503)
