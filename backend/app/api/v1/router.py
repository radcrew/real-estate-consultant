from fastapi import APIRouter

from app.api.v1.endpoints import ping

router = APIRouter()
router.include_router(ping.router)
