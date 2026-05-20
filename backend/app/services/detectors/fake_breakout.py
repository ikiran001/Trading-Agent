from dataclasses import dataclass

from app.services.detectors.breakout import detect_breakout


@dataclass
class FakeBreakoutResult:
    trap_zone: bool
    reason: str | None = None


def detect_fake_breakout(candles: list[dict]) -> FakeBreakoutResult:
    breakout = detect_breakout(candles)
    if not breakout.detected:
        return FakeBreakoutResult(False)
    if not breakout.volume_confirmed:
        return FakeBreakoutResult(True, "Breakout without volume confirmation")
    return FakeBreakoutResult(False)
