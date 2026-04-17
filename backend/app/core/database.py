from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

DB_ASYNC_ENGINE: AsyncEngine | None = None
DB_ASYNC_SESSION_MAKER: async_sessionmaker[AsyncSession] | None = None


def _async_database_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url.removeprefix("postgresql://")

    raise ValueError("DATABASE_URL must use postgresql://")


async def init_db() -> None:
    global DB_ASYNC_ENGINE, DB_ASYNC_SESSION_MAKER

    async_url = _async_database_url(settings.database_url)
    DB_ASYNC_ENGINE = create_async_engine(async_url, pool_pre_ping=True)
    DB_ASYNC_SESSION_MAKER = async_sessionmaker(
        DB_ASYNC_ENGINE,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


async def close_db() -> None:
    global DB_ASYNC_ENGINE, DB_ASYNC_SESSION_MAKER

    if DB_ASYNC_ENGINE is not None:
        await DB_ASYNC_ENGINE.dispose()

    DB_ASYNC_ENGINE = None
    DB_ASYNC_SESSION_MAKER = None


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    if DB_ASYNC_SESSION_MAKER is None:
        msg = "Database session requested before init_db()"
        raise RuntimeError(msg)

    async with DB_ASYNC_SESSION_MAKER() as session:
        yield session
