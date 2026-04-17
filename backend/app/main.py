from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.api.system import router as system_router
from app.core.config import settings
from app.core.database import close_db, init_db


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    yield
    await close_db()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        docs_url="/docs" if settings.is_dev_mode else None,
        redoc_url="/redoc" if settings.is_dev_mode else None,
        lifespan=lifespan,
    )
    app.include_router(system_router)
    app.include_router(api_router, prefix="/api")
    return app


app = create_app()
