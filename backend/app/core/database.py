from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

SUPABASE_ENGINE: AsyncEngine | None = None
ASYNC_SESSION_MAKER: async_sessionmaker[AsyncSession] | None = None


def _async_database_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url.removeprefix("postgresql://")

    raise ValueError("DATABASE_URL must use postgresql://")


async def init_db() -> None:
    global SUPABASE_ENGINE, ASYNC_SESSION_MAKER

    async_url = _async_database_url(settings.database_url)
    SUPABASE_ENGINE = create_async_engine(async_url, pool_pre_ping=True)
    ASYNC_SESSION_MAKER = async_sessionmaker(
        SUPABASE_ENGINE,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


async def close_db() -> None:
    global SUPABASE_ENGINE, ASYNC_SESSION_MAKER

    if SUPABASE_ENGINE is not None:
        await SUPABASE_ENGINE.dispose()

    SUPABASE_ENGINE = None
    ASYNC_SESSION_MAKER = None


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    if ASYNC_SESSION_MAKER is None:
        msg = "Database session requested before init_db()"
        raise RuntimeError(msg)

    async with ASYNC_SESSION_MAKER() as session:
        yield session
