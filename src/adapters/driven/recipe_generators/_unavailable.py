from typing import override

from src.domain.entities import RecipeContent
from src.domain.errors import RecipeGenerationUnavailableError
from src.domain.ports import GenerationContext, RecipeGenerator


class UnavailableRecipeGenerator(RecipeGenerator):
    @override
    async def create(self, request: str, context: GenerationContext) -> RecipeContent:
        raise RecipeGenerationUnavailableError

    @override
    async def rework(
        self,
        recipe: RecipeContent,
        instruction: str,
        context: GenerationContext,
    ) -> RecipeContent:
        raise RecipeGenerationUnavailableError
