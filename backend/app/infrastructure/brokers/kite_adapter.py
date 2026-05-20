import asyncio
from collections.abc import AsyncIterator
from datetime import datetime, timezone

from app.infrastructure.brokers.base import BrokerStreamAdapter

# Default index tokens (NSE) — overridden after instrument seed
DEFAULT_TOKENS = {
    "NIFTY": 256265,
    "BANKNIFTY": 260105,
    "FINNIFTY": 257801,
}


class KiteStreamAdapter(BrokerStreamAdapter):
    def __init__(self, api_key: str, access_token: str, token_map: dict[str, int] | None = None):
        self._api_key = api_key
        self._access_token = access_token
        self._token_map = token_map or DEFAULT_TOKENS
        self._reverse_map = {v: k for k, v in self._token_map.items()}
        self._queue: asyncio.Queue[dict] = asyncio.Queue()
        self._ticker = None
        self._connected = False

    async def connect(self) -> None:
        if not self._api_key or not self._access_token:
            raise ValueError("Kite API key and access token required")
        from kiteconnect import KiteTicker

        self._ticker = KiteTicker(self._api_key, self._access_token)

        def on_ticks(ws, ticks):
            for t in ticks:
                token = t.get("instrument_token")
                symbol = self._reverse_map.get(token, str(token))
                tick = {
                    "symbol": symbol,
                    "ltp": float(t.get("last_price", 0)),
                    "volume": int(t.get("volume_traded", t.get("volume", 0)) or 0),
                    "oi": t.get("oi"),
                    "bid": float(t.get("depth", {}).get("buy", [{}])[0].get("price", 0) if t.get("depth") else 0),
                    "ask": float(t.get("depth", {}).get("sell", [{}])[0].get("price", 0) if t.get("depth") else 0),
                    "ts": datetime.now(timezone.utc).isoformat(),
                }
                self._queue.put_nowait(tick)

        def on_connect(ws, response):
            self._connected = True

        def on_close(ws, code, reason):
            self._connected = False

        self._ticker.on_ticks = on_ticks
        self._ticker.on_connect = on_connect
        self._ticker.on_close = on_close
        self._ticker.connect(threaded=True)
        await asyncio.sleep(1)

    async def subscribe(self, instrument_tokens: list[int]) -> None:
        if self._ticker and self._connected:
            self._ticker.subscribe(instrument_tokens)
            self._ticker.set_mode(self._ticker.MODE_FULL, instrument_tokens)

    async def stream_ticks(self) -> AsyncIterator[dict]:
        while True:
            tick = await self._queue.get()
            yield tick

    async def disconnect(self) -> None:
        if self._ticker:
            self._ticker.close()
            self._connected = False


class SimulatedKiteAdapter(BrokerStreamAdapter):
    """Deterministic tick generator for dev/tests."""

    def __init__(self, symbols: list[str], ticks_per_second: float = 10):
        self._symbols = symbols
        self._interval = 1.0 / ticks_per_second
        self._prices = {s: 22000.0 if "NIFTY" in s else 48000.0 for s in symbols}

    async def connect(self) -> None:
        return

    async def subscribe(self, instrument_tokens: list[int]) -> None:
        return

    async def stream_ticks(self) -> AsyncIterator[dict]:
        import random

        while True:
            for symbol in self._symbols:
                delta = random.uniform(-5, 5)
                self._prices[symbol] += delta
                yield {
                    "symbol": symbol,
                    "ltp": round(self._prices[symbol], 2),
                    "volume": random.randint(100, 5000),
                    "oi": random.randint(100000, 500000),
                    "bid": round(self._prices[symbol] - 1, 2),
                    "ask": round(self._prices[symbol] + 1, 2),
                    "ts": datetime.now(timezone.utc).isoformat(),
                }
            await asyncio.sleep(self._interval)

    async def disconnect(self) -> None:
        return
