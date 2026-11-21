from datetime import date
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class MealSlot(StrEnum):
    BREAKFAST = "petit_dej"
    LUNCH = "midi"
    SNACK = "gouter"
    DINNER = "soir"


class PlannedMeal(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    planned_on: date
    slot: MealSlot
    recipe_id: UUID
    cook: str | None = None
    note: str = ""
