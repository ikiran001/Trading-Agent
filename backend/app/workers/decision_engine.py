import asyncio
from collections import defaultdict

from app.domain.signal import SignalAction
from app.infrastructure.db import create_session_factory, get_engine
from app.infrastructure.redis_bus import RedisBus
from app.repositories.signal_repository import SignalRepository
from app.services.decision_engine import DecisionEngine
from app.services.mtf_analyzer import MTFAnalysis
from app.services.risk_manager import RiskManager
from app.workers._runner import run_worker

_state: dict[str, dict] = defaultdict(dict)
_engine = DecisionEngine()
_DEBOUNCE: dict[str, float] = {}


async def main_loop(settings):
    bus = await RedisBus.from_url(settings.redis_url)
    risk = RiskManager(
        confidence_threshold=settings.confidence_threshold,
        max_daily_loss_pct=settings.max_daily_loss_pct,
        max_consecutive_losses=settings.max_consecutive_losses,
        min_rr_ratio=settings.min_rr_ratio,
    )
    session_factory = create_session_factory(get_engine())

    async def on_technical(channel: str, data: dict):
        symbol = data.get("symbol", "")
        _state[symbol]["technical"] = data
        await _maybe_emit(settings, bus, risk, session_factory, symbol)

    async def on_options(channel: str, data: dict):
        symbol = channel.split(":")[-1]
        _state[symbol]["options"] = data
        await _maybe_emit(settings, bus, risk, session_factory, symbol)

    async def on_sentiment(channel: str, data: dict):
        _state["__global__"]["sentiment"] = data
        for symbol in list(_state.keys()):
            if symbol != "__global__":
                await _maybe_emit(settings, bus, risk, session_factory, symbol)

    async def on_sector(channel: str, data: dict):
        _state["__global__"]["sector"] = data

    async def on_webhook(channel: str, data: dict):
        sym = data.get("symbol", "")
        _state[sym]["tv"] = data
        await _maybe_emit(settings, bus, risk, session_factory, sym)

    await bus.psubscribe("analysis:technical:*", on_technical)
    await bus.psubscribe("option_chain:*", on_options)
    await bus.subscribe("sentiment:aggregate", on_sentiment)
    await bus.subscribe("sector:heatmap", on_sector)
    await bus.subscribe("webhook:tradingview", on_webhook)

    while True:
        await asyncio.sleep(3600)


async def _maybe_emit(settings, bus, risk, session_factory, symbol: str):
    import time

    if symbol == "__global__":
        return
    now = time.time()
    if now - _DEBOUNCE.get(symbol, 0) < 0.2:
        return
    _DEBOUNCE[symbol] = now

    tech = _state[symbol].get("technical", {})
    opts = _state[symbol].get("options", {})
    global_sent = _state.get("__global__", {}).get("sentiment", {})
    global_sec = _state.get("__global__", {}).get("sector", {})
    tv = _state[symbol].get("tv")

    mtf_data = tech.get("mtf")
    mtf = MTFAnalysis(**mtf_data) if mtf_data else None

    signal = _engine.fuse(
        symbol=symbol,
        indicators=tech.get("indicators"),
        mtf=mtf,
        options_score=opts.get("score", 50),
        sector_score=global_sec.get("top_score", 50),
        sentiment_score=global_sent.get("score", 50),
        tv_confirm=bool(tv),
        candles_1m=None,
        data_stale=opts.get("data_stale", False),
    )
    if not signal or signal.signal == SignalAction.HOLD:
        return

    decision = risk.approve(signal, adx=(tech.get("indicators") or {}).get("adx", 25))
    if not decision.approved:
        return

    async with session_factory() as session:
        await SignalRepository(session).create(signal)

    await bus.publish("signal:new", signal.to_dict())


def main():
    asyncio.run(run_worker(main_loop))


if __name__ == "__main__":
    main()
