from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class BrokerStreamAdapter(ABC):
    @abstractmethod
    async def connect(self) -> None: ...

    @abstractmethod
    async def subscribe(self, instrument_tokens: list[int]) -> None: ...

    @abstractmethod
    async def stream_ticks(self) -> AsyncIterator[dict]: ...

    @abstractmethod
    async def disconnect(self) -> None: ...
