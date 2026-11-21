from uuid import UUID

from src.domain.entities import Recipe, RecipeContent, RecipeSource, RecipeTag
from src.domain.errors import NotFoundError
from src.domain.household import Household
from src.domain.ports import RecipeRepository


class RecipeService:
    def __init__(self, repository: RecipeRepository, household: Household) -> None:
        self._repository = repository
        self._household = household

    async def list_recipes(
        self,
        member: str | None = None,
        tag: RecipeTag | None = None,
        quick_only: bool = False,
    ) -> list[Recipe]:
        recipes = await self._repository.list_all()
        if member is not None:
            known = self._household.ensure_member(member)
            recipes = [recipe for recipe in recipes if recipe.concerns(known)]
        if tag is not None:
            recipes = [recipe for recipe in recipes if tag in recipe.tags]
        if quick_only:
            recipes = [recipe for recipe in recipes if recipe.is_quick]
        return sorted(recipes, key=lambda recipe: recipe.title.lower())

    async def get(self, recipe_id: UUID) -> Recipe:
        recipe = await self._repository.get(recipe_id)
        if recipe is None:
            raise NotFoundError("Recette", recipe_id)
        return recipe

    async def create(
        self,
        content: RecipeContent,
        cooks: list[str],
        fans: list[str],
        source: RecipeSource,
    ) -> Recipe:
        recipe = Recipe(
            **content.model_dump(),
            cooks=self._household.ensure_members(cooks),
            fans=self._household.ensure_members(fans),
            source=source,
        )
        await self._repository.save(recipe)
        return recipe

    async def replace_content(self, recipe_id: UUID, content: RecipeContent) -> Recipe:
        recipe = await self.get(recipe_id)
        recipe.replace_content(content)
        await self._repository.save(recipe)
        return recipe

    async def set_members(
        self,
        recipe_id: UUID,
        cooks: list[str],
        fans: list[str],
    ) -> Recipe:
        recipe = await self.get(recipe_id)
        recipe.cooks = self._household.ensure_members(cooks)
        recipe.fans = self._household.ensure_members(fans)
        await self._repository.save(recipe)
        return recipe

    async def set_preference(
        self,
        recipe_id: UUID,
        member: str,
        can_cook: bool | None,
        likes: bool | None,
    ) -> Recipe:
        recipe = await self.get(recipe_id)
        recipe.set_preference(self._household.ensure_member(member), can_cook, likes)
        await self._repository.save(recipe)
        return recipe

    async def delete(self, recipe_id: UUID) -> None:
        await self.get(recipe_id)
        await self._repository.delete(recipe_id)
