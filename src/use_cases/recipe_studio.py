from datetime import date
from uuid import UUID

from src.domain.constants import DEFAULT_RECIPE_REQUEST, EXPIRING_SOON_DAYS
from src.domain.entities import Recipe, RecipeContent, Season, StockKind
from src.domain.errors import NotFoundError
from src.domain.household import Household
from src.domain.ports import (
    GenerationContext,
    HouseholdNoteRepository,
    RecipeGenerator,
    RecipeRepository,
    StockRepository,
)
from src.domain.seasons import season_of

_COOKING_KINDS = (StockKind.INGREDIENT, StockKind.STAPLE)


def _member_tastes(members: list[str], recipes: list[Recipe]) -> list[str]:
    lines: list[str] = []
    for member in members:
        liked = [recipe.title for recipe in recipes if member in recipe.fans]
        disliked = [recipe.title for recipe in recipes if member in recipe.dislikes]
        if liked:
            lines.append(f"{member} aime : {', '.join(liked)}")
        if disliked:
            lines.append(f"{member} n'aime pas : {', '.join(disliked)}")
    return lines


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
        season: Season | None = None,
        stock_only: bool = False,
    ) -> GenerationContext:
        stock = [item for item in await self._stock.list_all() if item.kind in _COOKING_KINDS and item.is_available]
        recipes = await self._recipes.list_all()
        return GenerationContext(
            members=self._household.members,
            member=self._household.ensure_member(member) if member else None,
            quick=quick,
            season=season or season_of(today),
            available_ingredients=[item.name for item in stock] if use_stock else [],
            expiring_ingredients=[item.name for item in stock if item.expires_within(today, EXPIRING_SOON_DAYS)],
            household_notes=[note.text for note in await self._notes.list_all()],
            member_tastes=_member_tastes(self._household.members, recipes),
            existing_titles=[recipe.title for recipe in recipes],
            stock_only=stock_only and use_stock,
        )

    async def draft_new(
        self,
        request: str,
        member: str | None,
        quick: bool,
        use_stock: bool,
        today: date,
        season: Season | None = None,
        stock_only: bool = False,
    ) -> RecipeContent:
        context = await self._context(member, quick, use_stock, today, season, stock_only)
        return await self._generator.create(request.strip() or DEFAULT_RECIPE_REQUEST, context)

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
