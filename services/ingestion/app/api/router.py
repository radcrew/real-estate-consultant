from fastapi import APIRouter

from app.api.ingest import router as ingest_router
from app.api.jobs import router as jobs_router

api_router = APIRouter()
api_router.include_router(ingest_router)
api_router.include_router(jobs_router)
