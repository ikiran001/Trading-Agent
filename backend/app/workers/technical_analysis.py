import asyncio
from collections import defaultdict

from app.infrastructure.redis_bus import RedisBus
from app.services.detectors.breakout import detect_breakout
from app.services.indicators import compute_indicators
from app.services.mtf_analyzer import analyze_mtf
from app.workers._runner import run_worker

_candles: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
_DEBOUNCE: dict[str, float] = {}


async def main_loop(settings):
    bus = await RedisBus.from_url(settings.redis_url)

    async def on_candle(channel: str, data: dict):
        parts = channel.split(":")
        if len(parts) < 3:
            return
        symbol, tf = parts[1], parts[2]
        buf = _candles[symbol][tf]
        buf.append(data)
        if len(buf) > 200:
            buf.pop(0)

        import time

        now = time.time()
        if now - _DEBOUNCE.get(symbol, 0) < 0.1:
            return
        _DEBOUNCE[symbol] = now

        candles_1m = list(_candles[symbol].get("1m", []))
        indicators = compute_indicators(candles_1m)
        mtf = analyze_mtf({tf: list(_candles[symbol][tf]) for tf in _candles[symbol]})
        breakout = detect_breakout(candles_1m) if candles_1m else None

        payload = {
            "symbol": symbol,
            "indicators": indicators.to_dict() if indicators else None,
            "mtf": mtf.to_dict(),
            "breakout": {
                "detected": breakout.detected if breakout else False,
                "direction": breakout.direction if breakout else "none",
            },
        }
        await bus.publish(f"analysis:technical:{symbol}", payload)
        await bus.set_cache(f"cache:analysis:{symbol}", payload)

    await bus.psubscribe("candle:*", on_candle)
    while True:
        await asyncio.sleep(3600)


def main():
    asyncio.run(run_worker(main_loop))


if __name__ == "__main__":
    main()
