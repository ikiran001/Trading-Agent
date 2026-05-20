from datetime import datetime, timedelta, timezone

from app.services.candle_aggregator import CandleAggregator


def test_1m_bar_close():
    agg = CandleAggregator()
    base = datetime(2026, 5, 20, 10, 0, 0, tzinfo=timezone.utc)
    closed = []
    for i in range(65):
        ts = (base + timedelta(seconds=i * 5)).isoformat()
        bars = agg.on_tick({"symbol": "NIFTY", "ltp": 22000 + i, "volume": 100, "ts": ts})
        closed.extend(bars)
    assert len(closed) >= 1
    assert closed[0].timeframe == "1m"
    assert closed[0].symbol == "NIFTY"
