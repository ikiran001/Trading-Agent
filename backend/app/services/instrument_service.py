from app.infrastructure.brokers.kite_adapter import DEFAULT_TOKENS
from app.repositories.instrument_repository import InstrumentRepository


class InstrumentService:
    def __init__(self, repo: InstrumentRepository):
        self._repo = repo

    async def seed_defaults(self, symbols: list[str]) -> None:
        for symbol in symbols:
            token = DEFAULT_TOKENS.get(symbol)
            if token:
                await self._repo.upsert(symbol=symbol, token=token)

    async def resolve_tokens(self, symbols: list[str]) -> list[int]:
        await self.seed_defaults(symbols)
        mapping = await self._repo.get_tokens(symbols)
        return [mapping[s] for s in symbols if s in mapping]
