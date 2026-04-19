from fastapi import APIRouter, Depends

from app.api.v1.endpoints import auth, intake_sessions, ping, questions, search_profiles
from app.core.deps import get_current_user

router = APIRouter()
router.include_router(auth.router)
router.include_router(ping.router)

protected = APIRouter(dependencies=[Depends(get_current_user)])
protected.include_router(questions.router)
protected.include_router(intake_sessions.router)
protected.include_router(search_profiles.router)
router.include_router(protected)
