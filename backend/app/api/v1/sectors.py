from fastapi import APIRouter, Request

router = APIRouter(tags=["sectors"])


@router.get("/sectors")
async def get_sectors(request: Request):
    from app.infrastructure.redis_bus import RedisBus

    settings = request.app.state.settings
    bus = await RedisBus.from_url(settings.redis_url)
    data = await bus.get_cache("cache:sector:heatmap")
    await bus.close()
    return data or {"sectors": []}
