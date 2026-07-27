from fastapi import APIRouter

from . import avatar, password, profile, saved

# api_keys is mounted separately under JWT-only auth (see app.api.v1.router).

router = APIRouter(prefix="/account", tags=["account"])
router.include_router(profile.router)
router.include_router(password.router)
router.include_router(avatar.router)
router.include_router(saved.router)
