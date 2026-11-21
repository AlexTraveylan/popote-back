from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities import HouseholdNote


class HouseholdNoteRepository(ABC):
    @abstractmethod
    async def list_all(self) -> list[HouseholdNote]:
        pass

    @abstractmethod
    async def save(self, note: HouseholdNote) -> None:
        pass

    @abstractmethod
    async def delete(self, note_id: UUID) -> None:
        pass
