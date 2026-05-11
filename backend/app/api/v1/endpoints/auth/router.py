from fastapi import APIRouter

from . import sign_in, sign_up

router = APIRouter(prefix="/auth", tags=["auth"])
router.include_router(sign_up.router)
router.include_router(sign_in.router)
