from fastapi import APIRouter, Request

router = APIRouter(tags=["market"])


@router.get("/market/{symbol}")
async def get_market(symbol: str, request: Request):
    from app.infrastructure.redis_bus import RedisBus

    settings = request.app.state.settings
    bus = await RedisBus.from_url(settings.redis_url)
    analysis = await bus.get_cache(f"cache:analysis:{symbol.upper()}")
    candles = {}
    for tf in ["1m", "5m", "15m"]:
        c = await bus.get_cache(f"cache:candle:{symbol.upper()}:{tf}")
        if c:
            candles[tf] = c
    await bus.close()
    return {"symbol": symbol.upper(), "analysis": analysis, "latest_candles": candles}
