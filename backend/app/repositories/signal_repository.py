from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Signal
from app.domain.signal import SignalCreate


class SignalRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, signal: SignalCreate) -> Signal:
        row = Signal(
            id=signal.id,
            signal=signal.signal.value,
            category=signal.category.value,
            symbol=signal.symbol,
            instrument=signal.instrument,
            entry=signal.entry,
            stop_loss=signal.stop_loss,
            target_1=signal.target_1,
            target_2=signal.target_2,
            confidence=signal.confidence,
            risk_level=signal.risk_level,
            market_condition=signal.market_condition,
            holding_time=signal.holding_time,
            reasons=signal.reasons,
            payload=signal.to_dict(),
            data_stale=signal.data_stale,
        )
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return row

    async def list_recent(self, limit: int = 50, active_only: bool = False) -> list[Signal]:
        q = select(Signal).order_by(Signal.created_at.desc()).limit(limit)
        if active_only:
            q = q.where(Signal.status == "active")
        result = await self._session.execute(q)
        return list(result.scalars().all())
