from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from src.domain.entities import CookLog


class CookLogRepository(ABC):
    @abstractmethod
    async def list_between(self, start: date, end: date) -> list[CookLog]:
        pass

    @abstractmethod
    async def get(self, log_id: UUID) -> CookLog | None:
        pass

    @abstractmethod
    async def save(self, log: CookLog) -> None:
        pass

    @abstractmethod
    async def delete(self, log_id: UUID) -> None:
        pass
