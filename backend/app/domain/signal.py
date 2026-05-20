from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class SignalAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class SignalCategory(str, Enum):
    SCALP = "SCALP"
    INTRADAY = "INTRADAY"
    SWING = "SWING"


class SignalCreate(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    signal: SignalAction
    category: SignalCategory
    symbol: str
    instrument: str | None = None
    entry: float | None = None
    stop_loss: float | None = None
    target_1: float | None = None
    target_2: float | None = None
    confidence: int
    risk_level: str = "MEDIUM"
    market_condition: str = "NEUTRAL"
    holding_time: str | None = None
    reasons: list[str] = Field(default_factory=list)
    data_stale: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
