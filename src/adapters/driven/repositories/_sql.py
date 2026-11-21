from datetime import date
from typing import override
from uuid import UUID

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlmodel import col

from src.adapters.driven.db.models import (
    CookLogRecord,
    HouseholdNoteRecord,
    PlannedMealRecord,
    RecipeRecord,
    ShoppingTripRecord,
    StockItemRecord,
)
from src.domain.entities import CookLog, HouseholdNote, PlannedMeal, Recipe, ShoppingTrip, StockItem
from src.domain.ports import (
    CookLogRepository,
    HouseholdNoteRepository,
    PlannedMealRepository,
    RecipeRepository,
    ShoppingTripRepository,
    StockRepository,
)

from ._sql_document_store import SqlDocumentStore, payload_of


def _stock_record(item: StockItem) -> StockItemRecord:
    return StockItemRecord(id=item.id, name=item.name, payload=payload_of(item))


def _recipe_record(recipe: Recipe) -> RecipeRecord:
    return RecipeRecord(id=recipe.id, title=recipe.title, payload=payload_of(recipe))


def _log_record(log: CookLog) -> CookLogRecord:
    return CookLogRecord(id=log.id, cooked_on=log.cooked_on, payload=payload_of(log))


def _trip_record(trip: ShoppingTrip) -> ShoppingTripRecord:
    return ShoppingTripRecord(id=trip.id, shopped_on=trip.shopped_on, payload=payload_of(trip))


def _meal_record(meal: PlannedMeal) -> PlannedMealRecord:
    return PlannedMealRecord(id=meal.id, planned_on=meal.planned_on, payload=payload_of(meal))


def _note_record(note: HouseholdNote) -> HouseholdNoteRecord:
    return HouseholdNoteRecord(id=note.id, created_at=note.created_at, payload=payload_of(note))


class SqlStockRepository(StockRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._store = SqlDocumentStore(session_factory, StockItemRecord, StockItem, _stock_record)

    @override
    async def list_all(self) -> list[StockItem]:
        return await self._store.select()

    @override
    async def get(self, item_id: UUID) -> StockItem | None:
        return await self._store.get(item_id)

    @override
    async def save(self, item: StockItem) -> None:
        await self._store.upsert([item])

    @override
    async def save_many(self, items: list[StockItem]) -> None:
        await self._store.upsert(items)

    @override
    async def delete(self, item_id: UUID) -> None:
        await self._store.delete(item_id)


class SqlRecipeRepository(RecipeRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._store = SqlDocumentStore(session_factory, RecipeRecord, Recipe, _recipe_record)

    @override
    async def list_all(self) -> list[Recipe]:
        return await self._store.select()

    @override
    async def get(self, recipe_id: UUID) -> Recipe | None:
        return await self._store.get(recipe_id)

    @override
    async def save(self, recipe: Recipe) -> None:
        await self._store.upsert([recipe])

    @override
    async def delete(self, recipe_id: UUID) -> None:
        await self._store.delete(recipe_id)

    @override
    async def count(self) -> int:
        return await self._store.count()


class SqlCookLogRepository(CookLogRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._store = SqlDocumentStore(session_factory, CookLogRecord, CookLog, _log_record)

    @override
    async def list_between(self, start: date, end: date) -> list[CookLog]:
        return await self._store.select(
            col(CookLogRecord.cooked_on) >= start,
            col(CookLogRecord.cooked_on) <= end,
        )

    @override
    async def get(self, log_id: UUID) -> CookLog | None:
        return await self._store.get(log_id)

    @override
    async def save(self, log: CookLog) -> None:
        await self._store.upsert([log])

    @override
    async def delete(self, log_id: UUID) -> None:
        await self._store.delete(log_id)


class SqlShoppingTripRepository(ShoppingTripRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._store = SqlDocumentStore(session_factory, ShoppingTripRecord, ShoppingTrip, _trip_record)

    @override
    async def list_all(self) -> list[ShoppingTrip]:
        return await self._store.select()

    @override
    async def get(self, trip_id: UUID) -> ShoppingTrip | None:
        return await self._store.get(trip_id)

    @override
    async def save(self, trip: ShoppingTrip) -> None:
        await self._store.upsert([trip])

    @override
    async def delete(self, trip_id: UUID) -> None:
        await self._store.delete(trip_id)


class SqlPlannedMealRepository(PlannedMealRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._store = SqlDocumentStore(session_factory, PlannedMealRecord, PlannedMeal, _meal_record)

    @override
    async def list_between(self, start: date, end: date) -> list[PlannedMeal]:
        return await self._store.select(
            col(PlannedMealRecord.planned_on) >= start,
            col(PlannedMealRecord.planned_on) <= end,
        )

    @override
    async def get(self, meal_id: UUID) -> PlannedMeal | None:
        return await self._store.get(meal_id)

    @override
    async def save(self, meal: PlannedMeal) -> None:
        await self._store.upsert([meal])

    @override
    async def delete(self, meal_id: UUID) -> None:
        await self._store.delete(meal_id)


class SqlHouseholdNoteRepository(HouseholdNoteRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._store = SqlDocumentStore(session_factory, HouseholdNoteRecord, HouseholdNote, _note_record)

    @override
    async def list_all(self) -> list[HouseholdNote]:
        return await self._store.select()

    @override
    async def save(self, note: HouseholdNote) -> None:
        await self._store.upsert([note])

    @override
    async def delete(self, note_id: UUID) -> None:
        await self._store.delete(note_id)
