from app.domain.signal import SignalAction
from app.services.decision_engine import DecisionEngine
from app.services.mtf_analyzer import MTFAnalysis


def test_high_alignment_buy_confidence():
    engine = DecisionEngine()
    mtf = MTFAnalysis(symbol="NIFTY", trend_alignment_score=70, conflicts=[])
    sig = engine.fuse(
        symbol="NIFTY",
        indicators={
            "ema_bullish": True,
            "price": 22100,
            "vwap": 22000,
            "volume_ratio": 2.0,
            "adx": 28,
        },
        mtf=mtf,
        options_score=70,
        sector_score=70,
        sentiment_score=65,
        candles_1m=_bullish_candles(),
    )
    assert sig is not None
    assert sig.confidence >= 60


def test_fake_breakout_reduces_confidence():
    engine = DecisionEngine()
    candles = _bullish_candles()
    candles[-1]["volume"] = 1
    sig = engine.fuse(symbol="NIFTY", indicators={"price": 22100, "vwap": 22000, "volume_ratio": 0.5, "adx": 28}, mtf=None, candles_1m=candles)
    if sig:
        assert sig.confidence < 80 or sig.signal == SignalAction.HOLD


def _bullish_candles():
    candles = []
    for i in range(25):
        candles.append({
            "symbol": "NIFTY",
            "open": 22000 + i,
            "high": 22010 + i,
            "low": 21990 + i,
            "close": 22005 + i,
            "volume": 1000 if i < 24 else 5000,
        })
    return candles
