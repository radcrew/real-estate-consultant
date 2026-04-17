from fastapi import APIRouter

from app.api.v1.endpoints import auth, ping, seed
from app.core.config import settings

router = APIRouter()
router.include_router(auth.router)
router.include_router(ping.router)
if settings.is_dev_mode:
    router.include_router(seed.router)
