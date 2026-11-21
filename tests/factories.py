from typing import override

from src.adapters.driven.repositories import (
    InMemoryCookLogRepository,
    InMemoryHouseholdNoteRepository,
    InMemoryPlannedMealRepository,
    InMemoryRecipeRepository,
    InMemoryShoppingTripRepository,
    InMemoryStockRepository,
)
from src.container import Container
from src.domain.entities import RecipeContent, RecipeIngredient, RecipeTag, Season
from src.domain.household import Household
from src.domain.ports import GenerationContext, RecipeGenerator

MEMBERS = ["Alex", "Sam"]


class FakeRecipeGenerator(RecipeGenerator):
    def __init__(self) -> None:
        self.contexts: list[GenerationContext] = []
        self.requests: list[str] = []

    @override
    async def create(self, request: str, context: GenerationContext) -> RecipeContent:
        self.contexts.append(context)
        self.requests.append(request)
        return RecipeContent(
            title=f"Idée : {request}",
            summary="Générée pour les tests",
            prep_minutes=20,
            ingredients=[RecipeIngredient(name=name, quantity=100, unit="g") for name in context.available_ingredients],
            steps=["Cuisiner."],
            tags=[RecipeTag.QUICK],
            seasons=[context.season],
        )

    @override
    async def rework(
        self,
        recipe: RecipeContent,
        instruction: str,
        context: GenerationContext,
    ) -> RecipeContent:
        self.contexts.append(context)
        self.requests.append(instruction)
        return recipe.model_copy(update={"title": f"{recipe.title} ({instruction})"})


def build_container(generator: RecipeGenerator | None = None) -> Container:
    return Container(
        engine=None,
        household=Household(MEMBERS),
        stock_repo=InMemoryStockRepository(),
        recipe_repo=InMemoryRecipeRepository(),
        cook_log_repo=InMemoryCookLogRepository(),
        trip_repo=InMemoryShoppingTripRepository(),
        plan_repo=InMemoryPlannedMealRepository(),
        note_repo=InMemoryHouseholdNoteRepository(),
        recipe_generator=generator or FakeRecipeGenerator(),
    )


def recipe_content(
    title: str,
    ingredients: list[tuple[str, float | None, str | None]],
    prep_minutes: int = 20,
    tags: list[RecipeTag] | None = None,
    seasons: list[Season] | None = None,
) -> RecipeContent:
    return RecipeContent(
        title=title,
        prep_minutes=prep_minutes,
        ingredients=[RecipeIngredient(name=name, quantity=quantity, unit=unit) for name, quantity, unit in ingredients],
        steps=["Préparer.", "Servir."],
        tags=tags or [],
        seasons=seasons or [],
    )
