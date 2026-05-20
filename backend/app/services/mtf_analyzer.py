from dataclasses import dataclass


@dataclass
class MTFAnalysis:
    symbol: str
    trend_alignment_score: int  # -100 to 100
    conflicts: list[str]

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "trend_alignment_score": self.trend_alignment_score,
            "conflicts": self.conflicts,
        }


def analyze_mtf(candles_by_tf: dict[str, list[dict]]) -> MTFAnalysis:
    symbol = ""
    scores: list[int] = []
    conflicts: list[str] = []

    for tf, candles in candles_by_tf.items():
        if not candles:
            continue
        symbol = candles[-1].get("symbol", symbol) or symbol
        if len(candles) < 3:
            continue
        direction = 1 if candles[-1]["close"] > candles[-3]["close"] else -1
        weight = {"1m": 1, "3m": 1, "5m": 2, "15m": 3, "30m": 4, "60m": 5}.get(tf, 1)
        scores.append(direction * weight * 10)

    if not scores:
        return MTFAnalysis(symbol or "UNKNOWN", 0, [])

    alignment = max(-100, min(100, sum(scores) // max(len(scores), 1)))
    if scores and max(scores) > 0 and min(scores) < 0:
        conflicts.append("Timeframe trend conflict detected")

    return MTFAnalysis(symbol=symbol or "UNKNOWN", trend_alignment_score=alignment, conflicts=conflicts)
