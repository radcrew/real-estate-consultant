from fastapi import APIRouter

from . import api_keys, avatar, password, profile, saved

router = APIRouter(prefix="/account", tags=["account"])
router.include_router(profile.router)
router.include_router(password.router)
router.include_router(avatar.router)
router.include_router(saved.router)
router.include_router(api_keys.router)
