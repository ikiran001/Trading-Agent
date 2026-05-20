import asyncio

import pytest

from app.infrastructure.redis_bus import RedisBus


@pytest.mark.asyncio
async def test_pubsub_roundtrip(fake_redis):
    bus = RedisBus(fake_redis)
    received = []

    async def handler(channel, data):
        received.append((channel, data))

    await bus.subscribe("tick:NIFTY", handler)
    await bus.publish("tick:NIFTY", {"ltp": 23650.5})
    await asyncio.sleep(0.1)
    assert received[0][1]["ltp"] == 23650.5
