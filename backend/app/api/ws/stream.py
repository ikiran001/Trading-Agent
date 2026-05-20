import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config import get_settings
from app.infrastructure.redis_bus import RedisBus

router = APIRouter()


@router.websocket("/ws/v1/stream")
async def websocket_stream(websocket: WebSocket):
    await websocket.accept()
    settings = get_settings()
    bus = await RedisBus.from_url(settings.redis_url)
    queue: asyncio.Queue = asyncio.Queue()

    async def forward(channel: str, data: dict):
        msg_type = "signal" if channel == "signal:new" else "market"
        if channel.startswith("candle:"):
            msg_type = "candle"
        elif channel.startswith("analysis:"):
            msg_type = "analysis"
        elif channel == "sector:heatmap":
            msg_type = "sector"
        elif channel == "sentiment:aggregate":
            msg_type = "sentiment"
        await queue.put({"type": msg_type, "channel": channel, "payload": data})

    await bus.subscribe("signal:new", forward)
    await bus.psubscribe("candle:*", forward)
    await bus.psubscribe("analysis:technical:*", forward)
    await bus.subscribe("sector:heatmap", forward)
    await bus.subscribe("sentiment:aggregate", forward)

    async def sender():
        while True:
            msg = await queue.get()
            await websocket.send_text(json.dumps(msg, default=str))

    task = asyncio.create_task(sender())
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        task.cancel()
    finally:
        await bus.close()
