from fastapi import APIRouter

from . import avatar, password, profile, saved

router = APIRouter(prefix="/account", tags=["account"])
router.include_router(profile.router)
router.include_router(password.router)
router.include_router(avatar.router)
router.include_router(saved.router)
