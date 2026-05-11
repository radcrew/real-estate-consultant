from fastapi import APIRouter

from . import profile, password

router = APIRouter(prefix="/account", tags=["account"])
router.include_router(profile.router)
router.include_router(password.router)
