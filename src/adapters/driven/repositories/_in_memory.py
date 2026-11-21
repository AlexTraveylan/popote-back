from datetime import date
from typing import override
from uuid import UUID

from src.domain.entities import CookLog, HouseholdNote, PlannedMeal, Recipe, ShoppingTrip, StockItem
from src.domain.ports import (
    CookLogRepository,
    HouseholdNoteRepository,
    PlannedMealRepository,
    RecipeRepository,
    ShoppingTripRepository,
    StockRepository,
)


class InMemoryStockRepository(StockRepository):
    def __init__(self) -> None:
        self._items: dict[UUID, StockItem] = {}

    @override
    async def list_all(self) -> list[StockItem]:
        return [item.model_copy(deep=True) for item in self._items.values()]

    @override
    async def get(self, item_id: UUID) -> StockItem | None:
        item = self._items.get(item_id)
        return item.model_copy(deep=True) if item else None

    @override
    async def save(self, item: StockItem) -> None:
        self._items[item.id] = item.model_copy(deep=True)

    @override
    async def save_many(self, items: list[StockItem]) -> None:
        for item in items:
            await self.save(item)

    @override
    async def delete(self, item_id: UUID) -> None:
        self._items.pop(item_id, None)


class InMemoryRecipeRepository(RecipeRepository):
    def __init__(self) -> None:
        self._recipes: dict[UUID, Recipe] = {}

    @override
    async def list_all(self) -> list[Recipe]:
        return [recipe.model_copy(deep=True) for recipe in self._recipes.values()]

    @override
    async def get(self, recipe_id: UUID) -> Recipe | None:
        recipe = self._recipes.get(recipe_id)
        return recipe.model_copy(deep=True) if recipe else None

    @override
    async def save(self, recipe: Recipe) -> None:
        self._recipes[recipe.id] = recipe.model_copy(deep=True)

    @override
    async def delete(self, recipe_id: UUID) -> None:
        self._recipes.pop(recipe_id, None)

    @override
    async def count(self) -> int:
        return len(self._recipes)


class InMemoryCookLogRepository(CookLogRepository):
    def __init__(self) -> None:
        self._logs: dict[UUID, CookLog] = {}

    @override
    async def list_between(self, start: date, end: date) -> list[CookLog]:
        return [log for log in self._logs.values() if start <= log.cooked_on <= end]

    @override
    async def get(self, log_id: UUID) -> CookLog | None:
        return self._logs.get(log_id)

    @override
    async def save(self, log: CookLog) -> None:
        self._logs[log.id] = log

    @override
    async def delete(self, log_id: UUID) -> None:
        self._logs.pop(log_id, None)


class InMemoryShoppingTripRepository(ShoppingTripRepository):
    def __init__(self) -> None:
        self._trips: dict[UUID, ShoppingTrip] = {}

    @override
    async def list_all(self) -> list[ShoppingTrip]:
        return list(self._trips.values())

    @override
    async def get(self, trip_id: UUID) -> ShoppingTrip | None:
        return self._trips.get(trip_id)

    @override
    async def save(self, trip: ShoppingTrip) -> None:
        self._trips[trip.id] = trip

    @override
    async def delete(self, trip_id: UUID) -> None:
        self._trips.pop(trip_id, None)


class InMemoryPlannedMealRepository(PlannedMealRepository):
    def __init__(self) -> None:
        self._meals: dict[UUID, PlannedMeal] = {}

    @override
    async def list_between(self, start: date, end: date) -> list[PlannedMeal]:
        return [meal for meal in self._meals.values() if start <= meal.planned_on <= end]

    @override
    async def get(self, meal_id: UUID) -> PlannedMeal | None:
        return self._meals.get(meal_id)

    @override
    async def save(self, meal: PlannedMeal) -> None:
        self._meals[meal.id] = meal

    @override
    async def delete(self, meal_id: UUID) -> None:
        self._meals.pop(meal_id, None)


class InMemoryHouseholdNoteRepository(HouseholdNoteRepository):
    def __init__(self) -> None:
        self._notes: dict[UUID, HouseholdNote] = {}

    @override
    async def list_all(self) -> list[HouseholdNote]:
        return list(self._notes.values())

    @override
    async def save(self, note: HouseholdNote) -> None:
        self._notes[note.id] = note

    @override
    async def delete(self, note_id: UUID) -> None:
        self._notes.pop(note_id, None)
