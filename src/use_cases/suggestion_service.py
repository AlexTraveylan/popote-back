from datetime import timedelta

from src.domain.constants import RECENTLY_COOKED_DAYS
from src.domain.household import Household
from src.domain.ports import CookLogRepository, RecipeRepository, StockRepository
from src.domain.suggestions import Suggestion, SuggestionCriteria, rank_recipes


class SuggestionService:
    def __init__(
        self,
        recipe_repository: RecipeRepository,
        stock_repository: StockRepository,
        log_repository: CookLogRepository,
        household: Household,
    ) -> None:
        self._recipes = recipe_repository
        self._stock = stock_repository
        self._logs = log_repository
        self._household = household

    async def suggest(self, criteria: SuggestionCriteria) -> list[Suggestion]:
        if criteria.member is not None:
            criteria = criteria.model_copy(update={"member": self._household.ensure_member(criteria.member)})
        logs = await self._logs.list_between(
            criteria.today - timedelta(days=RECENTLY_COOKED_DAYS),
            criteria.today,
        )
        return rank_recipes(
            await self._recipes.list_all(),
            await self._stock.list_all(),
            logs,
            criteria,
        )
