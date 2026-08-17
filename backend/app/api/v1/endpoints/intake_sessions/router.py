from fastapi import APIRouter

from . import actions, jobs, sessions
from .answers.router import router as answers_router

router = APIRouter(prefix="/intake-sessions", tags=["intake-sessions"])
router.include_router(sessions.router)
router.include_router(actions.router)
router.include_router(answers_router)
router.include_router(jobs.router, prefix="/{session_id}/jobs", tags=["intake-jobs"])
