from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

_engine = None
_session_factory = None


def create_db_engine(database_url: str):
    return create_async_engine(database_url, echo=False, pool_pre_ping=True)


def create_session_factory(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def init_db(database_url: str) -> None:
    global _engine, _session_factory
    _engine = create_db_engine(database_url)
    _session_factory = create_session_factory(_engine)


def get_engine():
    if _engine is None:
        raise RuntimeError("Database not initialized")
    return _engine


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    if _session_factory is None:
        raise RuntimeError("Database not initialized")
    async with _session_factory() as session:
        yield session
