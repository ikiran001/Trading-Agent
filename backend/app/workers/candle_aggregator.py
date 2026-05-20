import asyncio

from app.infrastructure.redis_bus import RedisBus
from app.services.candle_aggregator import CandleAggregator
from app.workers._runner import run_worker

aggregator = CandleAggregator()


async def main_loop(settings):
    bus = await RedisBus.from_url(settings.redis_url)

    async def on_tick(channel: str, data: dict):
        for candle in aggregator.on_tick(data):
            await bus.publish(f"candle:{candle.symbol}:{candle.timeframe}", candle.to_dict())
            await bus.set_cache(f"cache:candle:{candle.symbol}:{candle.timeframe}", candle.to_dict())

    await bus.psubscribe("tick:*", on_tick)
    while True:
        await asyncio.sleep(3600)


def main():
    asyncio.run(run_worker(main_loop))


if __name__ == "__main__":
    main()
