from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(UTC)


class ConsumedIngredient(BaseModel):
    stock_item_id: UUID
    name: str
    quantity: float
    unit: str | None = None


class CookLog(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    recipe_id: UUID | None
    recipe_title: str
    cooked_by: str
    cooked_on: date
    servings: int
    consumed: list[ConsumedIngredient] = Field(default_factory=list)
    not_counted: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_now)
