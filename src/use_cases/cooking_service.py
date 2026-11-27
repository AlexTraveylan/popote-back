from datetime import date, timedelta
from uuid import UUID

from src.domain.availability import find_stock_item
from src.domain.entities import ConsumedIngredient, CookLog, Recipe, StockItem, StockKind
from src.domain.errors import NotFoundError
from src.domain.household import Household
from src.domain.ports import CookLogRepository, RecipeRepository, StockRepository


def _consume_ingredients(
    recipe: Recipe,
    servings: int,
    stock: list[StockItem],
) -> tuple[list[ConsumedIngredient], list[str], list[str], dict[UUID, StockItem]]:
    scale = servings / recipe.servings if recipe.servings > 0 else 1.0
    consumed: list[ConsumedIngredient] = []
    not_counted: list[str] = []
    missing: list[str] = []
    touched: dict[UUID, StockItem] = {}
    for ingredient in recipe.ingredients:
        item = find_stock_item(ingredient.name, stock)
        if item is None or not item.is_available:
            if not ingredient.optional:
                missing.append(ingredient.name)
            continue
        counted = ingredient.quantity and item.kind is StockKind.INGREDIENT
        amount = item.consume(ingredient.quantity * scale, ingredient.unit) if counted else None
        if amount is None:
            not_counted.append(ingredient.name)
            continue
        touched[item.id] = item
        consumed.append(ConsumedIngredient(stock_item_id=item.id, name=item.name, quantity=amount, unit=item.unit))
    return consumed, not_counted, missing, touched


class CookingService:
    def __init__(
        self,
        recipe_repository: RecipeRepository,
        stock_repository: StockRepository,
        log_repository: CookLogRepository,
        household: Household,
    ) -> None:
        self._recipes = recipe_repository
        self._stock = stock_repository
        self._logs = log_repository
        self._household = household

    async def cook(
        self,
        recipe_id: UUID,
        member: str,
        servings: int | None,
        cooked_on: date,
    ) -> CookLog:
        recipe = await self._recipes.get(recipe_id)
        if recipe is None:
            raise NotFoundError("Recette", recipe_id)
        cook = self._household.ensure_member(member)
        portions = servings or recipe.servings
        consumed, not_counted, missing, touched = _consume_ingredients(recipe, portions, await self._stock.list_all())
        await self._stock.save_many(list(touched.values()))
        log = CookLog(
            recipe_id=recipe.id,
            recipe_title=recipe.title,
            cooked_by=cook,
            cooked_on=cooked_on,
            servings=portions,
            consumed=consumed,
            not_counted=not_counted,
            missing=missing,
        )
        await self._logs.save(log)
        return log

    async def undo(self, log_id: UUID) -> None:
        log = await self._logs.get(log_id)
        if log is None:
            raise NotFoundError("Repas cuisiné", log_id)
        restored: list[StockItem] = []
        for line in log.consumed:
            item = await self._stock.get(line.stock_item_id)
            if item is not None:
                item.give_back(line.quantity)
                restored.append(item)
        await self._stock.save_many(restored)
        await self._logs.delete(log_id)

    async def history(self, start: date, end: date) -> list[CookLog]:
        logs = await self._logs.list_between(start, end)
        return sorted(logs, key=lambda log: (log.cooked_on, log.created_at), reverse=True)

    async def recent(self, today: date, days: int) -> list[CookLog]:
        return await self.history(today - timedelta(days=days), today)
