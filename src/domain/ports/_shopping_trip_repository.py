from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities import ShoppingTrip


class ShoppingTripRepository(ABC):
    @abstractmethod
    async def list_all(self) -> list[ShoppingTrip]:
        pass

    @abstractmethod
    async def get(self, trip_id: UUID) -> ShoppingTrip | None:
        pass

    @abstractmethod
    async def save(self, trip: ShoppingTrip) -> None:
        pass

    @abstractmethod
    async def delete(self, trip_id: UUID) -> None:
        pass
