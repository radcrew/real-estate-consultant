from fastapi import APIRouter

from . import confirm, password_reset, refresh, sign_in, sign_up

router = APIRouter(prefix="/auth", tags=["auth"])
router.include_router(sign_up.router)
router.include_router(sign_in.router)
router.include_router(confirm.router)
router.include_router(refresh.router)
router.include_router(password_reset.router)
