from datetime import UTC, datetime

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import check_db
from app.core.supabase_sdk import check_supabase

router = APIRouter(tags=["system"])

_started_at: str = datetime.now(UTC).isoformat()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/live")
def health_live() -> dict[str, str]:
    """Liveness: the process is up and the event loop is responsive."""
    return {"status": "ok"}


@router.get("/health/ready")
async def health_ready() -> JSONResponse:
    """Readiness: DB and Supabase are reachable. Returns 503 if either is down."""
    db_ok, supabase_ok = await check_db(), await check_supabase()
    all_ok = db_ok and supabase_ok
    body = {
        "status": "ok" if all_ok else "degraded",
        "checks": {"db": "ok" if db_ok else "fail", "supabase": "ok" if supabase_ok else "fail"},
        "version": settings.version,
        "git_sha": settings.git_sha or "unknown",
        "started_at": _started_at,
    }
    return JSONResponse(content=body, status_code=200 if all_ok else 503)
