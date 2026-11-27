from datetime import date, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from src.domain.availability import RecipeAvailability, assess_recipe
from src.domain.constants import DEFAULT_SUGGESTION_LIMIT
from src.domain.entities import (
    CookLog,
    HouseholdNote,
    MealSlot,
    PlannedMeal,
    Recipe,
    RecipeContent,
    RecipeTag,
    Season,
    ShoppingChannel,
    ShoppingTrip,
    StockCategory,
    StockItem,
    StockKind,
)
from src.domain.shopping import PantryOverview, ShoppingContext, week_start
from src.domain.suggestions import Suggestion, SuggestionCriteria
from src.use_cases.recipe_service import PreferenceOutcome
from src.use_cases.shopping_service import PurchaseRecord
from src.use_cases.stock_service import NewStockItem, StockItemPatch

from .dependencies import ContainerDep, DayDep
from .schemas import (
    CookRequest,
    HouseholdResponse,
    NewRecipeDraftRequest,
    NoteRequest,
    PlanMealRequest,
    RecipeCreateRequest,
    RecipeMembersRequest,
    RecipePreferenceRequest,
    ReworkDraftRequest,
    RunningLowRequest,
)

router = APIRouter(prefix="/api")


@router.get("/household")
async def get_household(container: ContainerDep) -> HouseholdResponse:
    return HouseholdResponse(
        members=container.household.members,
        stock_kinds=list(StockKind),
        stock_categories=list(StockCategory),
        shopping_channels=list(ShoppingChannel),
        meal_slots=list(MealSlot),
        recipe_generation_enabled=container.recipe_generation_enabled,
    )


@router.get("/stock")
async def list_stock(container: ContainerDep) -> list[StockItem]:
    return await container.stock_service.list_items()


@router.get("/stock/overview")
async def stock_overview(container: ContainerDep, day: DayDep) -> PantryOverview:
    return await container.stock_service.overview(day)


@router.post("/stock", status_code=status.HTTP_201_CREATED)
async def add_stock_item(container: ContainerDep, body: NewStockItem) -> StockItem:
    return await container.stock_service.add(body)


@router.patch("/stock/{item_id}")
async def update_stock_item(container: ContainerDep, item_id: UUID, body: StockItemPatch) -> StockItem:
    return await container.stock_service.update(item_id, body)


@router.put("/stock/{item_id}/running-low")
async def set_running_low(container: ContainerDep, item_id: UUID, body: RunningLowRequest) -> StockItem:
    return await container.stock_service.set_running_low(item_id, body.running_low)


@router.delete("/stock/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stock_item(container: ContainerDep, item_id: UUID) -> None:
    await container.stock_service.delete(item_id)


@router.get("/recipes")
async def list_recipes(
    container: ContainerDep,
    member: str | None = None,
    tag: RecipeTag | None = None,
    quick: bool = False,
    season: Season | None = None,
) -> list[Recipe]:
    return await container.recipe_service.list_recipes(member, tag, quick, season)


@router.post("/recipes", status_code=status.HTTP_201_CREATED)
async def create_recipe(container: ContainerDep, body: RecipeCreateRequest) -> Recipe:
    content = RecipeContent.model_validate(body.model_dump())
    return await container.recipe_service.create(content, body.cooks, body.fans, body.source)


@router.post("/recipes/drafts")
async def draft_new_recipe(container: ContainerDep, day: DayDep, body: NewRecipeDraftRequest) -> RecipeContent:
    return await container.recipe_studio.draft_new(
        body.request,
        body.member,
        body.quick,
        body.use_stock,
        day,
        body.season,
        body.stock_only,
    )


@router.get("/recipes/{recipe_id}")
async def get_recipe(container: ContainerDep, recipe_id: UUID) -> Recipe:
    return await container.recipe_service.get(recipe_id)


@router.get("/recipes/{recipe_id}/availability")
async def recipe_availability(container: ContainerDep, day: DayDep, recipe_id: UUID) -> RecipeAvailability:
    recipe = await container.recipe_service.get(recipe_id)
    return assess_recipe(recipe, await container.stock_service.list_items(), day)


@router.put("/recipes/{recipe_id}")
async def replace_recipe(container: ContainerDep, recipe_id: UUID, body: RecipeContent) -> Recipe:
    return await container.recipe_service.replace_content(recipe_id, body)


@router.put("/recipes/{recipe_id}/members")
async def set_recipe_members(container: ContainerDep, recipe_id: UUID, body: RecipeMembersRequest) -> Recipe:
    return await container.recipe_service.set_members(recipe_id, body.cooks, body.fans)


@router.put("/recipes/{recipe_id}/preferences")
async def set_recipe_preference(
    container: ContainerDep,
    recipe_id: UUID,
    body: RecipePreferenceRequest,
) -> PreferenceOutcome:
    return await container.recipe_service.set_preference(
        recipe_id,
        body.member,
        body.can_cook,
        body.likes,
        body.dislikes,
    )


@router.post("/recipes/{recipe_id}/drafts")
async def draft_recipe_rework(
    container: ContainerDep,
    day: DayDep,
    recipe_id: UUID,
    body: ReworkDraftRequest,
) -> RecipeContent:
    return await container.recipe_studio.draft_rework(recipe_id, body.instruction, body.member, day)


@router.delete("/recipes/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(container: ContainerDep, recipe_id: UUID) -> None:
    await container.recipe_service.delete(recipe_id)


@router.post("/recipes/{recipe_id}/cook", status_code=status.HTTP_201_CREATED)
async def cook_recipe(container: ContainerDep, recipe_id: UUID, body: CookRequest) -> CookLog:
    cooked_on = body.cooked_on or date.today()  # noqa: DTZ011
    return await container.cooking_service.cook(recipe_id, body.member, body.servings, cooked_on)


@router.get("/suggestions")
async def suggestions(
    container: ContainerDep,
    day: DayDep,
    member: str | None = None,
    quick: bool = False,
    liked: bool = False,
    tag: RecipeTag | None = None,
    season: Season | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = DEFAULT_SUGGESTION_LIMIT,
) -> list[Suggestion]:
    criteria = SuggestionCriteria(
        today=day,
        member=member,
        quick_only=quick,
        only_liked=liked,
        tag=tag,
        season=season,
        limit=limit,
    )
    return await container.suggestion_service.suggest(criteria)


@router.get("/cook-logs")
async def cook_logs(container: ContainerDep, start: date, end: date) -> list[CookLog]:
    return await container.cooking_service.history(start, end)


@router.get("/cook-logs/week")
async def cook_logs_this_week(container: ContainerDep, day: DayDep) -> list[CookLog]:
    monday = week_start(day)
    return await container.cooking_service.history(monday, monday + timedelta(days=6))


@router.delete("/cook-logs/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def undo_cook_log(container: ContainerDep, log_id: UUID) -> None:
    await container.cooking_service.undo(log_id)


@router.get("/plan")
async def list_plan(container: ContainerDep, start: date, end: date) -> list[PlannedMeal]:
    return await container.planning_service.between(start, end)


@router.post("/plan", status_code=status.HTTP_201_CREATED)
async def plan_meal(container: ContainerDep, body: PlanMealRequest) -> PlannedMeal:
    return await container.planning_service.plan(
        body.planned_on,
        body.slot,
        body.recipe_id,
        body.cook,
        body.note,
    )


@router.delete("/plan/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_planned_meal(container: ContainerDep, meal_id: UUID) -> None:
    await container.planning_service.remove(meal_id)


@router.get("/shopping/context")
async def shopping_context(container: ContainerDep, day: DayDep) -> ShoppingContext:
    return await container.shopping_service.context(day)


@router.get("/shopping/trips")
async def list_trips(container: ContainerDep) -> list[ShoppingTrip]:
    return await container.shopping_service.list_trips()


@router.post("/shopping/trips", status_code=status.HTTP_201_CREATED)
async def record_trip(container: ContainerDep, body: ShoppingTrip, update_stock: bool = True) -> ShoppingTrip:
    return await container.shopping_service.record_trip(body, update_stock)


@router.delete("/shopping/trips/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trip(container: ContainerDep, trip_id: UUID) -> None:
    await container.shopping_service.delete_trip(trip_id)


@router.get("/shopping/history")
async def purchase_history(
    container: ContainerDep,
    query: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[PurchaseRecord]:
    return await container.shopping_service.purchase_history(query, limit)


@router.get("/notes")
async def list_notes(container: ContainerDep) -> list[HouseholdNote]:
    return await container.note_service.list_notes()


@router.post("/notes", status_code=status.HTTP_201_CREATED)
async def add_note(container: ContainerDep, body: NoteRequest) -> HouseholdNote:
    return await container.note_service.add(body.text, body.author)


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(container: ContainerDep, note_id: UUID) -> None:
    await container.note_service.remove(note_id)
