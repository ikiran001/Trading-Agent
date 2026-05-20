from fastapi import APIRouter, Request

router = APIRouter(tags=["options"])


@router.get("/options/{symbol}")
async def get_options(symbol: str, request: Request):
    from app.infrastructure.redis_bus import RedisBus

    settings = request.app.state.settings
    bus = await RedisBus.from_url(settings.redis_url)
    # Latest option chain stored via worker cache pattern - use last published in-memory via subscribe not available; return placeholder from cache key if we add it
    data = await bus.get_cache(f"cache:option:{symbol.upper()}")
    await bus.close()
    return {"symbol": symbol.upper(), "snapshot": data or {}}
