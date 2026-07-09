import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.api.router import api_router
from app.api.system import router as system_router
from app.core.config import settings
from app.core.database import close_db, init_db
from app.core.db_safe import SupabaseRequestError
from app.core.logging import configure_logging
from app.core.middleware import RequestLoggingMiddleware
from app.core.supabase_sdk import close_supabase, init_supabase

configure_logging(settings.log_level, settings.swo_logs_url, settings.swo_token)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    await init_supabase()
    yield
    await close_supabase()
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
        request: Request,
        exc: SupabaseRequestError,
    ) -> JSONResponse:
        logger.warning(
            "Supabase request failed: %s",
            exc,
            extra={"error": type(exc).__name__, "path": request.url.path, "method": request.method},
        )
        return JSONResponse(
            status_code=502,
            content={"detail": "We couldn't reach the database. Please try again shortly."},
        )

    @app.exception_handler(HTTPException)
    async def http_exception_logging_handler(request: Request, exc: HTTPException) -> JSONResponse:
        level = logging.ERROR if exc.status_code >= 500 else logging.WARNING
        logger.log(
            level,
            "http_exception",
            extra={
                "error": type(exc).__name__,
                "status": exc.status_code,
                "path": request.url.path,
                "method": request.method,
                "detail": exc.detail,
            },
        )
        return await http_exception_handler(request, exc)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "unhandled_exception",
            exc_info=exc,
            extra={
                "error": type(exc).__name__,
                "path": request.url.path,
                "method": request.method,
            },
        )
        # Starlette routes handlers registered on the bare `Exception` class through
        # ServerErrorMiddleware, which sits *outside* CORSMiddleware — so this response
        # never picks up CORS headers on its own. Without them, the browser reports a
        # CORS failure instead of surfacing this 500, hiding the real error from the
        # frontend. Add the header manually, mirroring CORSMiddleware's own check.
        headers = {}
        origin = request.headers.get("origin")
        if origin and origin in settings.cors_origins:
            headers["Access-Control-Allow-Origin"] = origin
            headers["Vary"] = "Origin"
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error. Please try again later."},
            headers=headers,
        )

    app.include_router(system_router)
    app.include_router(api_router, prefix="/api")

    cors_origins = settings.cors_origins
    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.add_middleware(RequestLoggingMiddleware)

    return app


app = create_app()
