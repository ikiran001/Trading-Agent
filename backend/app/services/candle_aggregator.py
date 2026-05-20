from dataclasses import dataclass, field
from datetime import datetime, timezone

TIMEFRAMES = {"1m": 1, "3m": 3, "5m": 5, "15m": 15, "30m": 30, "60m": 60}


@dataclass
class CandleBar:
    symbol: str
    timeframe: str
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "ts": self.ts.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
        }


@dataclass
class _BuildingCandle:
    open: float
    high: float
    low: float
    close: float
    volume: float
    period_start: datetime


class CandleAggregator:
    def __init__(self):
        self._buffers: dict[tuple[str, str], _BuildingCandle] = {}

    def _period_start(self, ts: datetime, minutes: int) -> datetime:
        minute_bucket = (ts.minute // minutes) * minutes
        return ts.replace(minute=minute_bucket, second=0, microsecond=0)

    def on_tick(self, tick: dict) -> list[CandleBar]:
        symbol = tick["symbol"]
        price = float(tick["ltp"])
        volume = float(tick.get("volume", 0))
        ts_raw = tick.get("ts")
        if isinstance(ts_raw, str):
            ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
        else:
            ts = datetime.now(timezone.utc)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)

        closed: list[CandleBar] = []
        for tf, minutes in TIMEFRAMES.items():
            key = (symbol, tf)
            period = self._period_start(ts, minutes)
            buf = self._buffers.get(key)

            if buf is None:
                self._buffers[key] = _BuildingCandle(price, price, price, price, volume, period)
                continue

            if period > buf.period_start:
                closed.append(
                    CandleBar(
                        symbol=symbol,
                        timeframe=tf,
                        ts=buf.period_start,
                        open=buf.open,
                        high=buf.high,
                        low=buf.low,
                        close=buf.close,
                        volume=buf.volume,
                    )
                )
                self._buffers[key] = _BuildingCandle(price, price, price, price, volume, period)
            else:
                buf.high = max(buf.high, price)
                buf.low = min(buf.low, price)
                buf.close = price
                buf.volume += volume

        return closed
