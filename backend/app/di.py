from app.config import Settings, get_settings
from app.infrastructure.db import get_session, init_db
from app.infrastructure.redis_bus import RedisBus


def bootstrap(settings: Settings | None = None) -> Settings:
    settings = settings or get_settings()
    init_db(settings.database_url)
    return settings


async def get_redis_bus(settings: Settings | None = None) -> RedisBus:
    settings = settings or get_settings()
    return await RedisBus.from_url(settings.redis_url)
