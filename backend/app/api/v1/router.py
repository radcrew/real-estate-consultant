from fastapi import APIRouter, Depends

from app.api.v1.endpoints.account.router import router as account_router
from app.api.v1.endpoints.auth.router import router as auth_router
from app.api.v1.endpoints.filters.router import router as filters_router
from app.api.v1.endpoints.intake_sessions.router import router as intake_sessions_router
from app.api.v1.endpoints.listings.router import router as listings_router
from app.api.v1.endpoints.ping.router import router as ping_router
from app.api.v1.endpoints.questions.router import router as questions_router
from app.api.v1.endpoints.search.router import router as search_router
from app.core.deps import get_current_user

router = APIRouter()
router.include_router(auth_router)
router.include_router(ping_router)

protected = APIRouter(dependencies=[Depends(get_current_user)])
protected.include_router(questions_router)
protected.include_router(intake_sessions_router)
protected.include_router(search_router)
protected.include_router(listings_router)
protected.include_router(filters_router)
protected.include_router(account_router)
router.include_router(protected)
