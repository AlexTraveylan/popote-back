from datetime import UTC, date, datetime, timedelta
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, computed_field

from src.domain.names import normalize_name
from src.domain.units import convert, normalize_unit


def _now() -> datetime:
    return datetime.now(UTC)


class StockKind(StrEnum):
    INGREDIENT = "ingredient"
    STAPLE = "basique"
    BREAKFAST_SNACK = "petit_dej_gouter"
    FRUIT = "fruit"
    HOUSEHOLD = "maison"


class ShoppingChannel(StrEnum):
    DRIVE = "drive"
    FRESH_MARKET = "marche"
    OTHER = "autre"


class StockCategory(StrEnum):
    FRUITS_LEGUMES = "fruits_legumes"
    VIANDE_POISSON = "viande_poisson"
    CHARCUTERIE = "charcuterie"
    CREMERIE = "cremerie"
    EPICERIE_SALEE = "epicerie_salee"
    EPICERIE_SUCREE = "epicerie_sucree"
    SURGELES = "surgeles"
    PAIN = "pain"
    BOISSONS = "boissons"
    HYGIENE = "hygiene"
    ENTRETIEN = "entretien"
    ANIMAUX = "animaux"
    AUTRE = "autre"


def default_channel(kind: StockKind) -> ShoppingChannel:
    if kind is StockKind.FRUIT:
        return ShoppingChannel.FRESH_MARKET
    return ShoppingChannel.DRIVE


class StockItem(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    kind: StockKind = StockKind.INGREDIENT
    category: StockCategory = StockCategory.AUTRE
    channel: ShoppingChannel = ShoppingChannel.DRIVE
    quantity: float | None = None
    unit: str | None = None
    expires_on: date | None = None
    running_low: bool = False
    updated_at: datetime = Field(default_factory=_now)

    @property
    def key(self) -> str:
        return normalize_name(self.name)

    @property
    def is_tracked(self) -> bool:
        return self.quantity is not None

    @computed_field
    @property
    def is_out(self) -> bool:
        return self.quantity is not None and self.quantity <= 0

    @property
    def is_available(self) -> bool:
        return not self.is_out

    @computed_field
    @property
    def needs_restock(self) -> bool:
        return self.running_low or self.is_out

    def expires_within(self, today: date, days: int) -> bool:
        if self.expires_on is None or not self.is_available:
            return False
        return self.expires_on <= today + timedelta(days=days)

    def is_expired(self, today: date) -> bool:
        return self.expires_on is not None and self.is_available and self.expires_on < today

    def consume(self, quantity: float, unit: str | None) -> float | None:
        if self.quantity is None:
            return None
        converted = convert(quantity, unit, self.unit)
        if converted is None:
            return None
        consumed = min(converted, self.quantity)
        self.quantity = round(self.quantity - consumed, 3)
        self.updated_at = _now()
        return consumed

    def give_back(self, quantity: float) -> None:
        if self.quantity is None:
            return
        self.quantity = round(self.quantity + quantity, 3)
        self.updated_at = _now()

    def restock(
        self,
        quantity: float | None,
        unit: str | None,
        expires_on: date | None,
    ) -> None:
        was_empty = self.quantity is None or self.quantity <= 0
        self._add_quantity(quantity, unit)
        if expires_on is not None:
            self.expires_on = expires_on if was_empty or self.expires_on is None else min(self.expires_on, expires_on)
        self.running_low = False
        self.updated_at = _now()

    def _add_quantity(self, quantity: float | None, unit: str | None) -> None:
        if quantity is None:
            return
        if self.quantity is None:
            if self.kind is StockKind.INGREDIENT:
                self.quantity = quantity
                self.unit = normalize_unit(unit)
            return
        converted = convert(quantity, unit, self.unit)
        if converted is not None:
            self.quantity = round(max(self.quantity, 0) + converted, 3)
