import asyncio

from app.domain.signal import SignalCreate
from app.infrastructure.redis_bus import RedisBus
from app.infrastructure.telegram_notifier import format_alert, send_telegram
from app.workers._runner import run_worker

_last_alert: dict[str, float] = {}


async def main_loop(settings):
    bus = await RedisBus.from_url(settings.redis_url)

    async def on_signal(channel: str, data: dict):
        import time

        symbol = data.get("symbol", "unknown")
        if time.time() - _last_alert.get(symbol, 0) < 1.0:
            return
        _last_alert[symbol] = time.time()

        data = {k: v for k, v in data.items() if k in SignalCreate.model_fields}
        signal = SignalCreate.model_validate(data)

        msg = format_alert(signal)
        await send_telegram(settings.telegram_bot_token, settings.telegram_chat_id, msg)
        await bus.publish("alert:sent", {"symbol": symbol, "message": msg})

    await bus.subscribe("signal:new", on_signal)
    while True:
        await asyncio.sleep(3600)


def main():
    asyncio.run(run_worker(main_loop))


if __name__ == "__main__":
    main()
