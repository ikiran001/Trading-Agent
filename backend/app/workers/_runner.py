import asyncio

from app.config import get_settings
from app.di import bootstrap
from app.logging_config import setup_logging


async def run_worker(coro_factory):
    settings = bootstrap(get_settings())
    setup_logging(settings.log_level)
    await coro_factory(settings)
