from datetime import date
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, computed_field

from src.domain.constants import EXPIRING_SOON_DAYS
from src.domain.entities import Recipe, StockItem
from src.domain.names import names_match, normalize_name


class IngredientStatus(StrEnum):
    AVAILABLE = "disponible"
    RUNNING_LOW = "bientot_fini"
    MISSING = "manquant"


class IngredientCheck(BaseModel):
    name: str
    optional: bool
    status: IngredientStatus
    stock_item_id: UUID | None = None
    stock_name: str | None = None
    expiring_soon: bool = False


class RecipeAvailability(BaseModel):
    recipe_id: UUID
    checks: list[IngredientCheck]

    @computed_field
    @property
    def required_count(self) -> int:
        return sum(1 for check in self.checks if not check.optional)

    @computed_field
    @property
    def available_count(self) -> int:
        return sum(1 for check in self.checks if not check.optional and check.status != IngredientStatus.MISSING)

    @computed_field
    @property
    def ratio(self) -> float:
        if self.required_count == 0:
            return 1.0
        return round(self.available_count / self.required_count, 3)

    @computed_field
    @property
    def missing(self) -> list[str]:
        return [check.name for check in self.checks if not check.optional and check.status == IngredientStatus.MISSING]

    @computed_field
    @property
    def expiring(self) -> list[str]:
        return [check.name for check in self.checks if check.expiring_soon]


def find_stock_item(name: str, stock: list[StockItem]) -> StockItem | None:
    key = normalize_name(name)
    exact = [item for item in stock if item.key == key]
    candidates = exact or [item for item in stock if names_match(name, item.name)]
    if not candidates:
        return None
    available = [item for item in candidates if item.is_available]
    return (available or candidates)[0]


def _check_ingredient(
    name: str,
    optional: bool,
    stock: list[StockItem],
    today: date,
) -> IngredientCheck:
    item = find_stock_item(name, stock)
    if item is None or not item.is_available:
        return IngredientCheck(name=name, optional=optional, status=IngredientStatus.MISSING)
    status = IngredientStatus.RUNNING_LOW if item.running_low else IngredientStatus.AVAILABLE
    return IngredientCheck(
        name=name,
        optional=optional,
        status=status,
        stock_item_id=item.id,
        stock_name=item.name,
        expiring_soon=item.expires_within(today, EXPIRING_SOON_DAYS),
    )


def assess_recipe(recipe: Recipe, stock: list[StockItem], today: date) -> RecipeAvailability:
    return RecipeAvailability(
        recipe_id=recipe.id,
        checks=[
            _check_ingredient(ingredient.name, ingredient.optional, stock, today) for ingredient in recipe.ingredients
        ],
    )
