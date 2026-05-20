from fastapi import APIRouter, Request

router = APIRouter(tags=["sentiment"])


@router.get("/sentiment")
async def get_sentiment(request: Request):
    from app.infrastructure.redis_bus import RedisBus

    settings = request.app.state.settings
    bus = await RedisBus.from_url(settings.redis_url)
    data = await bus.get_cache("cache:sentiment:aggregate")
    await bus.close()
    return data or {"score": 50, "count": 0}
