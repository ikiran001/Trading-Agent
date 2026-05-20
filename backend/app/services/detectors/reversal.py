from dataclasses import dataclass


@dataclass
class ReversalResult:
    detected: bool
    direction: str  # bullish | bearish | none
    rsi_divergence: bool


def detect_reversal(candles: list[dict], rsi_values: list[float] | None = None) -> ReversalResult:
    if len(candles) < 10:
        return ReversalResult(False, "none", False)

    closes = [c["close"] for c in candles[-10:]]
    price_higher = closes[-1] > closes[0]

    if rsi_values and len(rsi_values) >= 10:
        rsi_higher = rsi_values[-1] > rsi_values[0]
        if price_higher and not rsi_higher:
            return ReversalResult(True, "bearish", True)
        if not price_higher and rsi_higher:
            return ReversalResult(True, "bullish", True)

    # MACD-style simple reversal: last 3 candles direction flip
    if closes[-1] < closes[-2] < closes[-3] and closes[-3] > closes[-4]:
        return ReversalResult(True, "bearish", False)
    if closes[-1] > closes[-2] > closes[-3] and closes[-3] < closes[-4]:
        return ReversalResult(True, "bullish", False)
    return ReversalResult(False, "none", False)
