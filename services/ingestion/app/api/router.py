from fastapi import APIRouter

from app.api.ingest import router as ingest_router

api_router = APIRouter()
api_router.include_router(ingest_router)
