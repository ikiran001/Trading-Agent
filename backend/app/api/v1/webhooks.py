import hashlib
import hmac
import json

from fastapi import APIRouter, HTTPException, Request

from app.infrastructure.redis_bus import RedisBus

router = APIRouter(tags=["webhooks"])


@router.post("/webhooks/tradingview")
async def tradingview_webhook(request: Request):
    settings = request.app.state.settings
    body = await request.body()
    signature = request.headers.get("X-TV-Signature", "")
    secret = settings.tradingview_webhook_secret

    if secret:
        expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON") from exc

    bus = await RedisBus.from_url(settings.redis_url)
    await bus.publish("webhook:tradingview", payload)
    await bus.close()
    return {"status": "accepted", "payload": payload}
