import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.api.system import router as system_router
from app.core.config import settings
from app.core.database import close_db, init_db
from app.core.db_safe import SupabaseRequestError

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    yield
    await close_db()


def create_app() -> FastAPI:
    # OpenAPI UI is enabled by default. Set ``docs_url=None`` here only if you intentionally ship
    # without UI.
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    @app.exception_handler(SupabaseRequestError)
    async def supabase_request_error_handler(
        _request: Request,
        exc: SupabaseRequestError,
    ) -> JSONResponse:
        logger.warning("Supabase request failed: %s", exc)
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    app.include_router(system_router)
    app.include_router(api_router, prefix="/api")

    cors_origins = [settings.frontend_origin]
    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    return app


app = create_app()
