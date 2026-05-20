from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Instrument


class InstrumentRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def upsert(self, symbol: str, token: int, exchange: str = "NSE", instrument_type: str = "INDEX", name: str | None = None) -> Instrument:
        result = await self._session.execute(select(Instrument).where(Instrument.symbol == symbol))
        row = result.scalar_one_or_none()
        if row:
            row.token = token
            row.exchange = exchange
            row.instrument_type = instrument_type
            if name:
                row.name = name
        else:
            row = Instrument(symbol=symbol, token=token, exchange=exchange, instrument_type=instrument_type, name=name)
            self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return row

    async def get_by_symbol(self, symbol: str) -> Instrument | None:
        result = await self._session.execute(select(Instrument).where(Instrument.symbol == symbol))
        return result.scalar_one_or_none()

    async def get_tokens(self, symbols: list[str]) -> dict[str, int]:
        result = await self._session.execute(select(Instrument).where(Instrument.symbol.in_(symbols)))
        rows = result.scalars().all()
        return {r.symbol: r.token for r in rows}
