from fastapi import FastAPI

from app.api.router import api_router
from app.api.system import router as system_router
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )
    app.include_router(system_router)
    app.include_router(api_router, prefix="/api")
    return app


app = create_app()
