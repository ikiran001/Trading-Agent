from dataclasses import dataclass

from app.services.candle_aggregator import CandleAggregator
from app.services.decision_engine import DecisionEngine
from app.services.indicators import compute_indicators
from app.services.mtf_analyzer import analyze_mtf


@dataclass
class BacktestResult:
    signals: list[dict]
    win_rate: float
    total: int


def replay_candles(symbol: str, ticks: list[dict]) -> BacktestResult:
    agg = CandleAggregator()
    engine = DecisionEngine()
    candles_1m: list[dict] = []
    signals: list[dict] = []

    for tick in ticks:
        tick["symbol"] = symbol
        for bar in agg.on_tick(tick):
            if bar.timeframe == "1m":
                d = bar.to_dict()
                candles_1m.append(d)
                if len(candles_1m) < 30:
                    continue
                indicators = compute_indicators(candles_1m[-60:])
                mtf = analyze_mtf({"1m": candles_1m[-60:]})
                sig = engine.fuse(
                    symbol=symbol,
                    indicators=indicators.to_dict() if indicators else None,
                    mtf=mtf,
                    candles_1m=candles_1m[-30:],
                )
                if sig and sig.signal.value != "HOLD" and sig.confidence >= 70:
                    signals.append(sig.to_dict())

    wins = sum(1 for s in signals if s.get("signal") == "BUY")
    total = len(signals)
    win_rate = (wins / total * 100) if total else 0.0
    return BacktestResult(signals=signals, win_rate=win_rate, total=total)
