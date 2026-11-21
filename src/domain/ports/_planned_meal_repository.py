from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from src.domain.entities import PlannedMeal


class PlannedMealRepository(ABC):
    @abstractmethod
    async def list_between(self, start: date, end: date) -> list[PlannedMeal]:
        pass

    @abstractmethod
    async def get(self, meal_id: UUID) -> PlannedMeal | None:
        pass

    @abstractmethod
    async def save(self, meal: PlannedMeal) -> None:
        pass

    @abstractmethod
    async def delete(self, meal_id: UUID) -> None:
        pass
