from fastapi import APIRouter

from app.api.v1.endpoints import auth, intake_sessions, ping, questions

router = APIRouter()
router.include_router(auth.router)
router.include_router(ping.router)
router.include_router(questions.router)
router.include_router(intake_sessions.router)
