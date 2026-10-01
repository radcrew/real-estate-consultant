from fastapi import APIRouter

from . import confirm, sign_in, sign_up

router = APIRouter(prefix="/auth", tags=["auth"])
router.include_router(sign_up.router)
router.include_router(sign_in.router)
router.include_router(confirm.router)
