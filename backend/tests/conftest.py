import asyncio

import pytest


@pytest.fixture
def fake_redis():
    import fakeredis.aioredis

    return fakeredis.aioredis.FakeRedis(decode_responses=True)
