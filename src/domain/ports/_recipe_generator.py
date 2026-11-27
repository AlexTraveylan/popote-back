from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from src.domain.entities import RecipeContent, Season


class GenerationContext(BaseModel):
    members: list[str]
    member: str | None = None
    quick: bool = False
    season: Season
    available_ingredients: list[str] = Field(default_factory=list)
    expiring_ingredients: list[str] = Field(default_factory=list)
    household_notes: list[str] = Field(default_factory=list)
    member_tastes: list[str] = Field(default_factory=list)
    stock_only: bool = False
    existing_titles: list[str] = Field(default_factory=list)


class RecipeGenerator(ABC):
    @abstractmethod
    async def create(self, request: str, context: GenerationContext) -> RecipeContent:
        pass

    @abstractmethod
    async def rework(
        self,
        recipe: RecipeContent,
        instruction: str,
        context: GenerationContext,
    ) -> RecipeContent:
        pass
