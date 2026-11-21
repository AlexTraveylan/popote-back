from datetime import date
from uuid import UUID

from src.domain.constants import EXPIRING_SOON_DAYS
from src.domain.entities import RecipeContent, StockKind
from src.domain.errors import NotFoundError
from src.domain.household import Household
from src.domain.ports import (
    GenerationContext,
    HouseholdNoteRepository,
    RecipeGenerator,
    RecipeRepository,
    StockRepository,
)

_COOKING_KINDS = (StockKind.INGREDIENT, StockKind.STAPLE)


class RecipeStudio:
    def __init__(
        self,
        generator: RecipeGenerator,
        recipe_repository: RecipeRepository,
        stock_repository: StockRepository,
        note_repository: HouseholdNoteRepository,
        household: Household,
    ) -> None:
        self._generator = generator
        self._recipes = recipe_repository
        self._stock = stock_repository
        self._notes = note_repository
        self._household = household

    async def _context(
        self,
        member: str | None,
        quick: bool,
        use_stock: bool,
        today: date,
    ) -> GenerationContext:
        stock = [item for item in await self._stock.list_all() if item.kind in _COOKING_KINDS and item.is_available]
        return GenerationContext(
            members=self._household.members,
            member=self._household.ensure_member(member) if member else None,
            quick=quick,
            available_ingredients=[item.name for item in stock] if use_stock else [],
            expiring_ingredients=[item.name for item in stock if item.expires_within(today, EXPIRING_SOON_DAYS)],
            household_notes=[note.text for note in await self._notes.list_all()],
            existing_titles=[recipe.title for recipe in await self._recipes.list_all()],
        )

    async def draft_new(
        self,
        request: str,
        member: str | None,
        quick: bool,
        use_stock: bool,
        today: date,
    ) -> RecipeContent:
        context = await self._context(member, quick, use_stock, today)
        return await self._generator.create(request, context)

    async def draft_rework(
        self,
        recipe_id: UUID,
        instruction: str,
        member: str | None,
        today: date,
    ) -> RecipeContent:
        recipe = await self._recipes.get(recipe_id)
        if recipe is None:
            raise NotFoundError("Recette", recipe_id)
        context = await self._context(member, quick=False, use_stock=True, today=today)
        return await self._generator.rework(RecipeContent(**recipe.model_dump()), instruction, context)
