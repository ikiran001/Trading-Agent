from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db import get_session
from app.repositories.signal_repository import SignalRepository

router = APIRouter(tags=["signals"])


@router.get("/signals")
async def list_signals(active: bool = False, limit: int = 50, session: AsyncSession = Depends(get_session)):
    repo = SignalRepository(session)
    rows = await repo.list_recent(limit=limit, active_only=active)
    return [
        {
            "id": str(r.id),
            "signal": r.signal,
            "category": r.category,
            "symbol": r.symbol,
            "instrument": r.instrument,
            "entry": r.entry,
            "stop_loss": r.stop_loss,
            "target_1": r.target_1,
            "target_2": r.target_2,
            "confidence": r.confidence,
            "risk_level": r.risk_level,
            "market_condition": r.market_condition,
            "holding_time": r.holding_time,
            "reasons": r.reasons,
            "status": r.status,
            "data_stale": r.data_stale,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
