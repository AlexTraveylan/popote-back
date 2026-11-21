from datetime import date, timedelta
from uuid import UUID

from pydantic import BaseModel

from src.domain.availability import find_stock_item
from src.domain.constants import COOKING_HISTORY_DAYS, UPCOMING_PLAN_DAYS
from src.domain.entities import PurchasedItem, ShoppingTrip, StockItem, StockKind, default_channel
from src.domain.errors import NotFoundError
from src.domain.household import Household
from src.domain.names import names_match
from src.domain.ports import (
    CookLogRepository,
    HouseholdNoteRepository,
    PlannedMealRepository,
    RecipeRepository,
    ShoppingTripRepository,
    StockRepository,
)
from src.domain.shopping import ShoppingContext, build_shopping_context


class PurchaseRecord(BaseModel):
    shopped_on: date
    store: str
    product_name: str
    stock_name: str
    packs: int
    unit_price: float | None


def _stock_amount(item: PurchasedItem) -> tuple[float | None, str | None]:
    if item.pack_quantity is not None:
        return item.total_quantity, item.pack_unit
    if item.kind is StockKind.INGREDIENT:
        return float(item.packs), "piece"
    return None, None


def _apply_purchase(item: PurchasedItem, stock: list[StockItem]) -> StockItem:
    existing = find_stock_item(item.stock_name, stock)
    target = existing or StockItem(
        name=item.stock_name.strip(),
        kind=item.kind,
        category=item.category,
        channel=default_channel(item.kind),
    )
    if existing is None:
        stock.append(target)
    quantity, unit = _stock_amount(item)
    target.restock(quantity, unit, item.expires_on)
    return target


class ShoppingService:
    def __init__(
        self,
        stock_repository: StockRepository,
        trip_repository: ShoppingTripRepository,
        recipe_repository: RecipeRepository,
        log_repository: CookLogRepository,
        plan_repository: PlannedMealRepository,
        note_repository: HouseholdNoteRepository,
        household: Household,
    ) -> None:
        self._stock = stock_repository
        self._trips = trip_repository
        self._recipes = recipe_repository
        self._logs = log_repository
        self._plan = plan_repository
        self._notes = note_repository
        self._household = household

    async def record_trip(self, trip: ShoppingTrip, update_stock: bool = True) -> ShoppingTrip:
        if update_stock:
            stock = await self._stock.list_all()
            touched = {target.id: target for target in (_apply_purchase(item, stock) for item in trip.items)}
            await self._stock.save_many(list(touched.values()))
        await self._trips.save(trip)
        return trip

    async def list_trips(self) -> list[ShoppingTrip]:
        trips = await self._trips.list_all()
        return sorted(trips, key=lambda trip: trip.shopped_on, reverse=True)

    async def get_trip(self, trip_id: UUID) -> ShoppingTrip:
        trip = await self._trips.get(trip_id)
        if trip is None:
            raise NotFoundError("Courses", trip_id)
        return trip

    async def delete_trip(self, trip_id: UUID) -> None:
        await self.get_trip(trip_id)
        await self._trips.delete(trip_id)

    async def purchase_history(self, query: str | None, limit: int) -> list[PurchaseRecord]:
        records = [
            PurchaseRecord(
                shopped_on=trip.shopped_on,
                store=trip.store,
                product_name=item.product_name,
                stock_name=item.stock_name,
                packs=item.packs,
                unit_price=item.unit_price,
            )
            for trip in await self.list_trips()
            for item in trip.items
            if query is None or names_match(query, item.stock_name) or query.lower() in item.product_name.lower()
        ]
        return records[:limit]

    async def context(self, today: date) -> ShoppingContext:
        return build_shopping_context(
            members=self._household.members,
            stock=await self._stock.list_all(),
            recipes=await self._recipes.list_all(),
            recent_logs=await self._logs.list_between(today - timedelta(days=COOKING_HISTORY_DAYS), today),
            plan=await self._plan.list_between(today, today + timedelta(days=UPCOMING_PLAN_DAYS)),
            trips=await self._trips.list_all(),
            notes=await self._notes.list_all(),
            today=today,
        )
