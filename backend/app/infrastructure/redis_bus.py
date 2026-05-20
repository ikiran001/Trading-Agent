import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any

import redis.asyncio as redis

Handler = Callable[[str, dict[str, Any]], Awaitable[None]]


class RedisBus:
    def __init__(self, client: redis.Redis):
        self._client = client
        self._pubsub: redis.client.PubSub | None = None
        self._handlers: dict[str, list[Handler]] = {}
        self._listener_task: asyncio.Task | None = None

    @classmethod
    async def from_url(cls, url: str) -> "RedisBus":
        client = redis.from_url(url, decode_responses=True)
        return cls(client)

    async def publish(self, channel: str, data: dict[str, Any]) -> None:
        await self._client.publish(channel, json.dumps(data, default=str))
        await self._dispatch_local(channel, data)

    async def _dispatch_local(self, channel: str, data: dict[str, Any]) -> None:
        if channel in self._handlers:
            for handler in self._handlers[channel]:
                await handler(channel, data)
        for pattern, handlers in self._handlers.items():
            if "*" in pattern and _match_pattern(pattern, channel):
                for handler in handlers:
                    await handler(channel, data)

    async def _ensure_pubsub(self) -> None:
        if self._pubsub is None:
            self._pubsub = self._client.pubsub()

    async def _start_listener(self) -> None:
        if self._listener_task is None:
            self._listener_task = asyncio.create_task(self._listen())

    async def subscribe(self, channel: str, handler: Handler) -> None:
        self._handlers.setdefault(channel, []).append(handler)
        await self._ensure_pubsub()
        assert self._pubsub is not None
        await self._pubsub.subscribe(channel)
        await self._start_listener()

    async def psubscribe(self, pattern: str, handler: Handler) -> None:
        self._handlers.setdefault(pattern, []).append(handler)
        await self._ensure_pubsub()
        assert self._pubsub is not None
        await self._pubsub.psubscribe(pattern)
        await self._start_listener()

    async def _listen(self) -> None:
        assert self._pubsub is not None

        async for message in self._pubsub.listen():
            if message["type"] not in ("message", "pmessage"):
                continue
            channel = message.get("channel") or message.get("pattern", "")
            if isinstance(channel, bytes):
                channel = channel.decode()
            try:
                data = json.loads(message["data"])
            except (json.JSONDecodeError, TypeError):
                continue
            await self._dispatch_local(channel, data)

    async def set_cache(self, key: str, data: dict[str, Any], ttl: int = 300) -> None:
        await self._client.setex(key, ttl, json.dumps(data, default=str))

    async def get_cache(self, key: str) -> dict[str, Any] | None:
        raw = await self._client.get(key)
        if not raw:
            return None
        return json.loads(raw)

    async def close(self) -> None:
        if self._listener_task:
            self._listener_task.cancel()
        if self._pubsub:
            await self._pubsub.close()
        await self._client.aclose()


def _match_pattern(pattern: str, channel: str) -> bool:
    if pattern.endswith("*"):
        return channel.startswith(pattern[:-1])
    return pattern == channel
