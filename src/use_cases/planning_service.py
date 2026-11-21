from datetime import date
from uuid import UUID

from src.domain.entities import HouseholdNote, MealSlot, PlannedMeal
from src.domain.errors import NotFoundError
from src.domain.household import Household
from src.domain.ports import HouseholdNoteRepository, PlannedMealRepository, RecipeRepository


class PlanningService:
    def __init__(
        self,
        plan_repository: PlannedMealRepository,
        recipe_repository: RecipeRepository,
        household: Household,
    ) -> None:
        self._plan = plan_repository
        self._recipes = recipe_repository
        self._household = household

    async def between(self, start: date, end: date) -> list[PlannedMeal]:
        meals = await self._plan.list_between(start, end)
        return sorted(meals, key=lambda meal: (meal.planned_on, list(MealSlot).index(meal.slot)))

    async def plan(
        self,
        planned_on: date,
        slot: MealSlot,
        recipe_id: UUID,
        cook: str | None,
        note: str = "",
    ) -> PlannedMeal:
        if await self._recipes.get(recipe_id) is None:
            raise NotFoundError("Recette", recipe_id)
        meal = PlannedMeal(
            planned_on=planned_on,
            slot=slot,
            recipe_id=recipe_id,
            cook=self._household.ensure_member(cook) if cook else None,
            note=note,
        )
        await self._plan.save(meal)
        return meal

    async def remove(self, meal_id: UUID) -> None:
        if await self._plan.get(meal_id) is None:
            raise NotFoundError("Repas prévu", meal_id)
        await self._plan.delete(meal_id)


class NoteService:
    def __init__(self, repository: HouseholdNoteRepository, household: Household) -> None:
        self._repository = repository
        self._household = household

    async def list_notes(self) -> list[HouseholdNote]:
        notes = await self._repository.list_all()
        return sorted(notes, key=lambda note: note.created_at)

    async def add(self, text: str, author: str | None) -> HouseholdNote:
        note = HouseholdNote(text=text.strip(), author=self._household.ensure_member(author) if author else None)
        await self._repository.save(note)
        return note

    async def remove(self, note_id: UUID) -> None:
        await self._repository.delete(note_id)
