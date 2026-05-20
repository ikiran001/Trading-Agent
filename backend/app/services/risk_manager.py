from dataclasses import dataclass

from app.domain.signal import SignalCreate


@dataclass
class RiskDecision:
    approved: bool
    reason: str | None = None


class RiskManager:
    def __init__(
        self,
        confidence_threshold: int = 70,
        max_daily_loss_pct: float = 2.0,
        max_consecutive_losses: int = 3,
        min_rr_ratio: float = 1.5,
    ):
        self.confidence_threshold = confidence_threshold
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_consecutive_losses = max_consecutive_losses
        self.min_rr_ratio = min_rr_ratio
        self.daily_pnl_pct = 0.0
        self.consecutive_losses = 0
        self.halted = False

    def approve(self, signal: SignalCreate, adx: float = 25.0) -> RiskDecision:
        if self.halted:
            return RiskDecision(False, "Trading halted for the day")
        if self.daily_pnl_pct <= -self.max_daily_loss_pct:
            self.halted = True
            return RiskDecision(False, "Max daily loss reached")
        if self.consecutive_losses >= self.max_consecutive_losses:
            self.halted = True
            return RiskDecision(False, "Max consecutive losses reached")
        if signal.confidence < self.confidence_threshold:
            return RiskDecision(False, f"Confidence {signal.confidence} below threshold")
        if signal.data_stale:
            return RiskDecision(False, "Stale market data")
        if signal.category.value == "INTRADAY" and adx < 20:
            return RiskDecision(False, "Sideways market — intraday blocked")
        if signal.entry and signal.stop_loss and signal.target_1:
            risk = abs(signal.entry - signal.stop_loss)
            reward = abs(signal.target_1 - signal.entry)
            if risk > 0 and reward / risk < self.min_rr_ratio:
                return RiskDecision(False, "Risk-reward below minimum")
        return RiskDecision(True)
