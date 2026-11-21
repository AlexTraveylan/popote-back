from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, computed_field, field_validator

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
    DESSERT = "dessert"
    BREAKFAST = "petit_dej"


_LEGACY_TAGS = frozenset({"saison"})


class Season(StrEnum):
    SPRING = "printemps"
    SUMMER = "ete"
    AUTUMN = "automne"
    WINTER = "hiver"


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
    seasons: list[Season] = Field(default_factory=list)

    @field_validator("tags", mode="before")
    @classmethod
    def _drop_legacy_tags(cls, value: Any) -> Any:
        if isinstance(value, list):
            return [tag for tag in value if tag not in _LEGACY_TAGS]
        return value

    @field_validator("seasons")
    @classmethod
    def _sort_seasons(cls, value: list[Season]) -> list[Season]:
        return [season for season in Season if season in value]

    def fits(self, season: Season) -> bool:
        return not self.seasons or season in self.seasons


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
        self.seasons = content.seasons
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
