from app.domain.signal import SignalAction, SignalCategory, SignalCreate
from app.services.risk_manager import RiskManager


def test_rejects_low_confidence():
    rm = RiskManager(confidence_threshold=70)
    sig = SignalCreate(signal=SignalAction.BUY, category=SignalCategory.INTRADAY, symbol="NIFTY", confidence=50)
    assert not rm.approve(sig).approved


def test_rejects_sideways_intraday():
    rm = RiskManager()
    sig = SignalCreate(signal=SignalAction.BUY, category=SignalCategory.INTRADAY, symbol="NIFTY", confidence=80)
    assert not rm.approve(sig, adx=15).approved
