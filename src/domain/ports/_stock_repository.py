from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities import StockItem


class StockRepository(ABC):
    @abstractmethod
    async def list_all(self) -> list[StockItem]:
        pass

    @abstractmethod
    async def get(self, item_id: UUID) -> StockItem | None:
        pass

    @abstractmethod
    async def save(self, item: StockItem) -> None:
        pass

    @abstractmethod
    async def save_many(self, items: list[StockItem]) -> None:
        pass

    @abstractmethod
    async def delete(self, item_id: UUID) -> None:
        pass
