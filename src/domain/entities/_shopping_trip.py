from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from ._stock_item import ShoppingChannel, StockCategory, StockKind


def _now() -> datetime:
    return datetime.now(UTC)


class PurchasedItem(BaseModel):
    product_name: str
    stock_name: str
    kind: StockKind = StockKind.INGREDIENT
    category: StockCategory = StockCategory.AUTRE
    packs: int = 1
    pack_quantity: float | None = None
    pack_unit: str | None = None
    unit_price: float | None = None
    expires_on: date | None = None

    @property
    def total_quantity(self) -> float | None:
        if self.pack_quantity is None:
            return None
        return self.pack_quantity * self.packs

    @property
    def total_price(self) -> float | None:
        if self.unit_price is None:
            return None
        return round(self.unit_price * self.packs, 2)


class ShoppingTrip(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    store: str
    channel: ShoppingChannel = ShoppingChannel.DRIVE
    shopped_on: date
    items: list[PurchasedItem]
    total: float | None = None
    notes: str = ""
    created_at: datetime = Field(default_factory=_now)

    @property
    def computed_total(self) -> float | None:
        if self.total is not None:
            return self.total
        prices = [item.total_price for item in self.items]
        if any(price is None for price in prices):
            return None
        return round(sum(price for price in prices if price is not None), 2)
