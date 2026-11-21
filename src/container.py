from sqlalchemy.ext.asyncio import AsyncEngine

from src.adapters.driven.db.database import create_engine, create_session_factory
from src.adapters.driven.recipe_generators import OpenAIRecipeGenerator, UnavailableRecipeGenerator
from src.adapters.driven.repositories import (
    SqlCookLogRepository,
    SqlHouseholdNoteRepository,
    SqlPlannedMealRepository,
    SqlRecipeRepository,
    SqlShoppingTripRepository,
    SqlStockRepository,
)
from src.config import get_settings
from src.domain.household import Household
from src.domain.ports import (
    CookLogRepository,
    HouseholdNoteRepository,
    PlannedMealRepository,
    RecipeGenerator,
    RecipeRepository,
    ShoppingTripRepository,
    StockRepository,
)
from src.use_cases.cooking_service import CookingService
from src.use_cases.planning_service import NoteService, PlanningService
from src.use_cases.recipe_service import RecipeService
from src.use_cases.recipe_studio import RecipeStudio
from src.use_cases.seed_database import SeedDatabase
from src.use_cases.shopping_service import ShoppingService
from src.use_cases.stock_service import StockService
from src.use_cases.suggestion_service import SuggestionService


class Container:
    def __init__(
        self,
        engine: AsyncEngine | None,
        household: Household,
        stock_repo: StockRepository,
        recipe_repo: RecipeRepository,
        cook_log_repo: CookLogRepository,
        trip_repo: ShoppingTripRepository,
        plan_repo: PlannedMealRepository,
        note_repo: HouseholdNoteRepository,
        recipe_generator: RecipeGenerator,
    ) -> None:
        self.engine = engine
        self.household = household
        self.recipe_generation_enabled = not isinstance(recipe_generator, UnavailableRecipeGenerator)
        self.stock_service = StockService(stock_repo, trip_repo)
        self.recipe_service = RecipeService(recipe_repo, household)
        self.cooking_service = CookingService(recipe_repo, stock_repo, cook_log_repo, household)
        self.suggestion_service = SuggestionService(recipe_repo, stock_repo, cook_log_repo, household)
        self.recipe_studio = RecipeStudio(recipe_generator, recipe_repo, stock_repo, note_repo, household)
        self.shopping_service = ShoppingService(
            stock_repo,
            trip_repo,
            recipe_repo,
            cook_log_repo,
            plan_repo,
            note_repo,
            household,
        )
        self.planning_service = PlanningService(plan_repo, recipe_repo, household)
        self.note_service = NoteService(note_repo, household)
        self.seed_database = SeedDatabase(recipe_repo, self.stock_service, trip_repo, note_repo, household)


def _build_recipe_generator(api_key: str, model: str) -> RecipeGenerator:
    if not api_key:
        return UnavailableRecipeGenerator()
    return OpenAIRecipeGenerator(api_key, model)


def _build_production_container() -> Container:
    settings = get_settings()
    engine = create_engine(settings.db)
    session_factory = create_session_factory(engine)
    return Container(
        engine=engine,
        household=Household(settings.HOUSEHOLD_MEMBERS),
        stock_repo=SqlStockRepository(session_factory),
        recipe_repo=SqlRecipeRepository(session_factory),
        cook_log_repo=SqlCookLogRepository(session_factory),
        trip_repo=SqlShoppingTripRepository(session_factory),
        plan_repo=SqlPlannedMealRepository(session_factory),
        note_repo=SqlHouseholdNoteRepository(session_factory),
        recipe_generator=_build_recipe_generator(settings.OPENAI_API_KEY, settings.OPENAI_MODEL),
    )


_container: Container | None = None


def get_container() -> Container:
    global _container
    if _container is None:
        _container = _build_production_container()
    return _container


def set_container(container: Container) -> None:
    global _container
    _container = container


def reset_container() -> None:
    global _container
    _container = None
