from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities import Recipe


class RecipeRepository(ABC):
    @abstractmethod
    async def list_all(self) -> list[Recipe]:
        pass

    @abstractmethod
    async def get(self, recipe_id: UUID) -> Recipe | None:
        pass

    @abstractmethod
    async def save(self, recipe: Recipe) -> None:
        pass

    @abstractmethod
    async def delete(self, recipe_id: UUID) -> None:
        pass

    @abstractmethod
    async def count(self) -> int:
        pass
