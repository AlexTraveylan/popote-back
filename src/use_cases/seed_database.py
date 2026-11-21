from pydantic import BaseModel, Field

from src.domain.entities import HouseholdNote, Recipe, RecipeContent, RecipeSource, ShoppingTrip
from src.domain.household import Household
from src.domain.ports import HouseholdNoteRepository, RecipeRepository, ShoppingTripRepository
from src.use_cases.stock_service import NewStockItem, StockService


class RecipeMembers(BaseModel):
    cooks: list[str] = Field(default_factory=list)
    fans: list[str] = Field(default_factory=list)


class SeedData(BaseModel):
    recipes: list[RecipeContent] = Field(default_factory=list)
    stock: list[NewStockItem] = Field(default_factory=list)
    trips: list[ShoppingTrip] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    recipe_members: dict[str, RecipeMembers] = Field(default_factory=dict)

    def merged_with(self, other: SeedData) -> SeedData:
        return SeedData(
            recipes=[*self.recipes, *other.recipes],
            stock=[*self.stock, *other.stock],
            trips=[*self.trips, *other.trips],
            notes=[*self.notes, *other.notes],
            recipe_members={**self.recipe_members, **other.recipe_members},
        )


class SeedReport(BaseModel):
    recipes: int = 0
    stock_items: int = 0
    trips: int = 0
    notes: int = 0


class SeedDatabase:
    def __init__(
        self,
        recipe_repository: RecipeRepository,
        stock_service: StockService,
        trip_repository: ShoppingTripRepository,
        note_repository: HouseholdNoteRepository,
        household: Household,
    ) -> None:
        self._recipes = recipe_repository
        self._stock = stock_service
        self._trips = trip_repository
        self._notes = note_repository
        self._household = household

    def _known(self, members: list[str]) -> list[str]:
        allowed = {member.lower(): member for member in self._household.members}
        return [allowed[member.lower()] for member in members if member.lower() in allowed]

    async def seed_if_empty(self, data: SeedData) -> SeedReport:
        if await self._recipes.count() > 0:
            return SeedReport()
        report = SeedReport()
        for new_item in data.stock:
            if await self._stock.find_by_name(new_item.name) is None:
                await self._stock.add(new_item)
                report.stock_items += 1
        for content in data.recipes:
            members = data.recipe_members.get(content.title, RecipeMembers())
            recipe = Recipe(
                **content.model_dump(),
                cooks=self._known(members.cooks),
                fans=self._known(members.fans),
                source=RecipeSource.SEED,
            )
            await self._recipes.save(recipe)
            report.recipes += 1
        for trip in data.trips:
            await self._trips.save(trip)
            report.trips += 1
        for text in data.notes:
            await self._notes.save(HouseholdNote(text=text))
            report.notes += 1
        return report
