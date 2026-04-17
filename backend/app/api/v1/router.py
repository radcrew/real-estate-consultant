from fastapi import APIRouter

from app.api.v1.endpoints import auth, ping

router = APIRouter()
router.include_router(auth.router)
router.include_router(ping.router)
