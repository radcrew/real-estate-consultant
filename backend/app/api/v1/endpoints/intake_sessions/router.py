from fastapi import APIRouter

from . import actions, sessions
from .answers.router import router as answers_router

router = APIRouter(prefix="/intake-sessions", tags=["intake-sessions"])
router.include_router(sessions.router)
router.include_router(actions.router)
router.include_router(answers_router)
