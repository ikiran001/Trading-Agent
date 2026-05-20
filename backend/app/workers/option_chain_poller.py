import asyncio
from datetime import datetime, timezone

from app.infrastructure.nse_option_chain import NSEOptionChainClient
from app.infrastructure.redis_bus import RedisBus
from app.services.options_analyzer import analyze_options
from app.utils.market_hours import is_market_hours
from app.workers._runner import run_worker

_client = NSEOptionChainClient()
_prev: dict[str, dict] = {}


async def main_loop(settings):
    bus = await RedisBus.from_url(settings.redis_url)
    while True:
        if is_market_hours():
            for symbol in settings.watchlist:
                try:
                    data = await _client.fetch(symbol)
                    analysis = analyze_options(data, _prev.get(symbol))
                    _prev[symbol] = data
                    payload = {
                        "symbol": symbol,
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "pcr": analysis.pcr,
                        "max_pain": analysis.max_pain,
                        "score": analysis.score(),
                        "trap_zone": analysis.trap_zone,
                        "data_stale": False,
                        "chain": data,
                    }
                    await bus.publish(f"option_chain:{symbol}", payload)
                    await bus.set_cache(
                        f"cache:option:{symbol}",
                        {"pcr": analysis.pcr, "max_pain": analysis.max_pain, "score": analysis.score()},
                    )
                except Exception:
                    _client.record_failure()
                    await bus.publish(
                        f"option_chain:{symbol}",
                        {"symbol": symbol, "score": 50, "data_stale": True},
                    )
            await asyncio.sleep(5)
        else:
            await asyncio.sleep(60)


def main():
    asyncio.run(run_worker(main_loop))


if __name__ == "__main__":
    main()
