from dataclasses import dataclass


@dataclass
class BreakoutResult:
    detected: bool
    direction: str  # "up" | "down" | "none"
    resistance: float
    volume_confirmed: bool


def detect_breakout(candles: list[dict], lookback: int = 20) -> BreakoutResult:
    if len(candles) < lookback + 1:
        return BreakoutResult(False, "none", 0.0, False)

    highs = [c["high"] for c in candles[-lookback - 1 : -1]]
    resistance = max(highs)
    last = candles[-1]
    close = last["close"]
    volumes = [c["volume"] for c in candles[-21:]]
    avg_vol = sum(volumes[:-1]) / max(len(volumes) - 1, 1)
    vol_confirmed = last["volume"] > 1.5 * avg_vol

    if close > resistance:
        return BreakoutResult(True, "up", resistance, vol_confirmed)
    lows = [c["low"] for c in candles[-lookback - 1 : -1]]
    support = min(lows)
    if close < support:
        return BreakoutResult(True, "down", support, vol_confirmed)
    return BreakoutResult(False, "none", resistance, vol_confirmed)
