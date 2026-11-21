from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

from src.domain.entities import MealSlot, RecipeContent, RecipeSource, ShoppingChannel, StockCategory, StockKind


class HouseholdResponse(BaseModel):
    members: list[str]
    stock_kinds: list[StockKind]
    stock_categories: list[StockCategory]
    shopping_channels: list[ShoppingChannel]
    meal_slots: list[MealSlot]
    recipe_generation_enabled: bool


class RecipeCreateRequest(RecipeContent):
    cooks: list[str] = Field(default_factory=list)
    fans: list[str] = Field(default_factory=list)
    source: RecipeSource = RecipeSource.MANUAL


class RecipeMembersRequest(BaseModel):
    cooks: list[str]
    fans: list[str]


class RecipePreferenceRequest(BaseModel):
    member: str
    can_cook: bool | None = None
    likes: bool | None = None


class NewRecipeDraftRequest(BaseModel):
    request: str = Field(min_length=3)
    member: str | None = None
    quick: bool = False
    use_stock: bool = True


class ReworkDraftRequest(BaseModel):
    instruction: str = Field(min_length=3)
    member: str | None = None


class CookRequest(BaseModel):
    member: str
    servings: int | None = Field(default=None, ge=1, le=30)
    cooked_on: date | None = None


class PlanMealRequest(BaseModel):
    planned_on: date
    slot: MealSlot
    recipe_id: UUID
    cook: str | None = None
    note: str = ""


class NoteRequest(BaseModel):
    text: str = Field(min_length=2)
    author: str | None = None


class RunningLowRequest(BaseModel):
    running_low: bool
