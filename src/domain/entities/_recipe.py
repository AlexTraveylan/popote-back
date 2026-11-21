from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, computed_field

from src.domain.constants import DEFAULT_SERVINGS, QUICK_RECIPE_MAX_MINUTES


def _now() -> datetime:
    return datetime.now(UTC)


class RecipeTag(StrEnum):
    QUICK = "rapide"
    VEGETARIAN = "vegetarien"
    FISH = "poisson"
    PERUVIAN = "peruvien"
    SIMMERED = "mijote"
    LIGHT = "leger"
    BATCH = "a_congeler"
    GUESTS = "invites"
    KIDS = "enfants"
    SEASONAL = "saison"
    DESSERT = "dessert"
    BREAKFAST = "petit_dej"


class RecipeSource(StrEnum):
    SEED = "seed"
    MANUAL = "manuel"
    OPENAI = "chatgpt"
    CLAUDE = "claude"


class RecipeIngredient(BaseModel):
    name: str
    quantity: float | None = None
    unit: str | None = None
    optional: bool = False


class RecipeContent(BaseModel):
    title: str
    summary: str = ""
    servings: int = DEFAULT_SERVINGS
    prep_minutes: int
    ingredients: list[RecipeIngredient]
    steps: list[str]
    tags: list[RecipeTag] = Field(default_factory=list)


class Recipe(RecipeContent):
    id: UUID = Field(default_factory=uuid4)
    cooks: list[str] = Field(default_factory=list)
    fans: list[str] = Field(default_factory=list)
    source: RecipeSource = RecipeSource.MANUAL
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

    @computed_field
    @property
    def is_quick(self) -> bool:
        return self.prep_minutes <= QUICK_RECIPE_MAX_MINUTES or RecipeTag.QUICK in self.tags

    def concerns(self, member: str) -> bool:
        return member in self.cooks or member in self.fans

    def replace_content(self, content: RecipeContent) -> None:
        self.title = content.title
        self.summary = content.summary
        self.servings = content.servings
        self.prep_minutes = content.prep_minutes
        self.ingredients = content.ingredients
        self.steps = content.steps
        self.tags = content.tags
        self.updated_at = _now()

    def set_preference(
        self,
        member: str,
        can_cook: bool | None,
        likes: bool | None,
    ) -> None:
        if can_cook is not None:
            self.cooks = _toggle(self.cooks, member, enabled=can_cook)
        if likes is not None:
            self.fans = _toggle(self.fans, member, enabled=likes)
        self.updated_at = _now()


def _toggle(members: list[str], member: str, *, enabled: bool) -> list[str]:
    without = [current for current in members if current != member]
    return [*without, member] if enabled else without
