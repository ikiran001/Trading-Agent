import asyncio

from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.infrastructure.brokers.kite_adapter import KiteStreamAdapter, SimulatedKiteAdapter
from app.infrastructure.db import create_session_factory, get_engine
from app.infrastructure.redis_bus import RedisBus
from app.repositories.instrument_repository import InstrumentRepository
from app.services.instrument_service import InstrumentService
from app.utils.market_hours import is_market_hours
from app.workers._runner import run_worker


@retry(wait=wait_exponential(min=1, max=60), stop=stop_after_attempt(10))
async def _connect_and_stream(settings, bus: RedisBus):
    if settings.use_tick_simulator or not settings.kite_access_token:
        adapter = SimulatedKiteAdapter(settings.watchlist, ticks_per_second=10)
    else:
        adapter = KiteStreamAdapter(settings.kite_api_key, settings.kite_access_token)

    session_factory = create_session_factory(get_engine())
    async with session_factory() as session:
        inst_svc = InstrumentService(InstrumentRepository(session))
        tokens = await inst_svc.resolve_tokens(settings.watchlist)

    await adapter.connect()
    if tokens:
        await adapter.subscribe(tokens)

    async for tick in adapter.stream_ticks():
        await bus.publish(f"tick:{tick['symbol']}", tick)


async def main_loop(settings):
    bus = await RedisBus.from_url(settings.redis_url)
    while True:
        if is_market_hours() or settings.use_tick_simulator:
            try:
                await _connect_and_stream(settings, bus)
            except Exception:
                await asyncio.sleep(5)
        else:
            await asyncio.sleep(30)


def main():
    asyncio.run(run_worker(main_loop))


if __name__ == "__main__":
    main()
