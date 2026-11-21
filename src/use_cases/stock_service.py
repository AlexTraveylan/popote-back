from datetime import UTC, date, datetime
from uuid import UUID

from pydantic import BaseModel

from src.domain.entities import ShoppingChannel, StockCategory, StockItem, StockKind, default_channel
from src.domain.errors import DuplicateStockItemError, NotFoundError
from src.domain.names import normalize_name
from src.domain.ports import ShoppingTripRepository, StockRepository
from src.domain.shopping import PantryOverview, build_pantry_overview
from src.domain.units import normalize_unit


class NewStockItem(BaseModel):
    name: str
    kind: StockKind = StockKind.INGREDIENT
    category: StockCategory = StockCategory.AUTRE
    channel: ShoppingChannel | None = None
    quantity: float | None = None
    unit: str | None = None
    expires_on: date | None = None
    running_low: bool = False


class StockItemPatch(BaseModel):
    name: str | None = None
    kind: StockKind | None = None
    category: StockCategory | None = None
    channel: ShoppingChannel | None = None
    quantity: float | None = None
    clear_quantity: bool = False
    unit: str | None = None
    expires_on: date | None = None
    clear_expiry: bool = False
    running_low: bool | None = None


class StockService:
    def __init__(
        self,
        stock_repository: StockRepository,
        trip_repository: ShoppingTripRepository,
    ) -> None:
        self._stock = stock_repository
        self._trips = trip_repository

    async def list_items(self) -> list[StockItem]:
        items = await self._stock.list_all()
        return sorted(items, key=lambda item: (item.kind, item.category, item.name.lower()))

    async def get(self, item_id: UUID) -> StockItem:
        item = await self._stock.get(item_id)
        if item is None:
            raise NotFoundError("Article", item_id)
        return item

    async def find_by_name(self, name: str) -> StockItem | None:
        key = normalize_name(name)
        return next((item for item in await self._stock.list_all() if item.key == key), None)

    async def add(self, new_item: NewStockItem) -> StockItem:
        if await self.find_by_name(new_item.name) is not None:
            raise DuplicateStockItemError(new_item.name)
        item = StockItem(
            name=new_item.name.strip(),
            kind=new_item.kind,
            category=new_item.category,
            channel=new_item.channel or default_channel(new_item.kind),
            quantity=new_item.quantity,
            unit=normalize_unit(new_item.unit),
            expires_on=new_item.expires_on,
            running_low=new_item.running_low,
        )
        await self._stock.save(item)
        return item

    async def update(self, item_id: UUID, patch: StockItemPatch) -> StockItem:
        item = await self.get(item_id)
        changes = patch.model_dump(exclude_none=True, exclude={"clear_quantity", "clear_expiry", "unit"})
        updated = item.model_copy(update=changes)
        if patch.unit is not None:
            updated.unit = normalize_unit(patch.unit)
        if patch.clear_quantity:
            updated.quantity = None
        if patch.clear_expiry:
            updated.expires_on = None
        updated.updated_at = datetime.now(UTC)
        await self._stock.save(updated)
        return updated

    async def set_running_low(self, item_id: UUID, running_low: bool) -> StockItem:
        return await self.update(item_id, StockItemPatch(running_low=running_low))

    async def delete(self, item_id: UUID) -> None:
        await self.get(item_id)
        await self._stock.delete(item_id)

    async def overview(self, today: date) -> PantryOverview:
        return build_pantry_overview(await self._stock.list_all(), await self._trips.list_all(), today)
