from datetime import date

import pytest
from faker import Faker

from src.domain.constants import DEFAULT_RECIPE_REQUEST
from src.domain.entities import RecipeSource, StockKind
from src.domain.suggestions import SuggestionCriteria
from src.use_cases.stock_service import NewStockItem
from tests.factories import MEMBERS, FakeRecipeGenerator, build_container, recipe_content

fake = Faker("fr_FR")
TODAY = date(2026, 11, 27)


class TestPreferences:
    async def test_like_and_dislike_are_exclusive(self) -> None:
        # Given
        container = build_container()
        recipe = await container.recipe_service.create(recipe_content(fake.word(), []), [], [], RecipeSource.SEED)

        # When
        await container.recipe_service.set_preference(recipe.id, "Alex", None, True)
        outcome = await container.recipe_service.set_preference(recipe.id, "alex", None, None, True)

        # Then
        assert outcome.recipe.fans == []
        assert outcome.recipe.dislikes == ["Alex"]
        assert not outcome.deleted

    async def test_recipe_is_deleted_when_every_member_dislikes_it(self) -> None:
        # Given
        container = build_container()
        recipe = await container.recipe_service.create(recipe_content(fake.word(), []), [], [], RecipeSource.SEED)

        # When
        outcomes = [
            await container.recipe_service.set_preference(recipe.id, member, None, None, True) for member in MEMBERS
        ]

        # Then
        assert [outcome.deleted for outcome in outcomes] == [False, True]
        assert await container.recipe_service.list_recipes() == []

    async def test_suggestions_hide_recipes_the_member_dislikes(self) -> None:
        # Given
        container = build_container()
        disliked = await container.recipe_service.create(recipe_content("Endives", []), [], [], RecipeSource.SEED)
        await container.recipe_service.create(recipe_content("Pâtes", []), [], [], RecipeSource.SEED)
        await container.recipe_service.set_preference(disliked.id, "Sam", None, None, True)

        # When
        for_sam = await container.suggestion_service.suggest(SuggestionCriteria(today=TODAY, member="Sam"))
        for_alex = await container.suggestion_service.suggest(SuggestionCriteria(today=TODAY, member="Alex"))

        # Then
        assert [suggestion.recipe.title for suggestion in for_sam] == ["Pâtes"]
        assert len(for_alex) == 2


class TestCookable:
    @pytest.mark.parametrize(
        ("stock", "cookable"),
        [(["pâtes", "lardons"], True), (["pâtes"], False)],
    )
    async def test_cookable_needs_every_required_ingredient(self, stock: list[str], cookable: bool) -> None:
        # Given
        container = build_container()
        for name in stock:
            await container.stock_service.add(NewStockItem(name=name, quantity=500, unit="g"))
        await container.recipe_service.create(
            recipe_content("Pâtes lardons", [("pâtes", 400, "g"), ("lardons", 150, "g")]),
            [],
            [],
            RecipeSource.SEED,
        )

        # When
        suggestions = await container.suggestion_service.suggest(SuggestionCriteria(today=TODAY))

        # Then
        assert suggestions[0].availability.cookable is cookable


class TestCookingSkipsConsumables:
    async def test_staples_are_never_decremented(self) -> None:
        # Given
        container = build_container()
        await container.stock_service.add(NewStockItem(name="farine", quantity=1000, unit="g"))
        await container.stock_service.add(
            NewStockItem(name="sucre", kind=StockKind.STAPLE, quantity=1000, unit="g"),
        )
        recipe = await container.recipe_service.create(
            recipe_content("Crêpes", [("farine", 250, "g"), ("sucre", 50, "g")]),
            [],
            [],
            RecipeSource.SEED,
        )

        # When
        log = await container.cooking_service.cook(recipe.id, "Alex", None, TODAY)
        stock = {item.name: item.quantity for item in await container.stock_service.list_items()}

        # Then
        assert stock == {"farine": 750, "sucre": 1000}
        assert log.not_counted == ["sucre"]


class TestStockOnlyGeneration:
    async def test_empty_request_uses_stock_only_and_member_tastes(self) -> None:
        # Given
        generator = FakeRecipeGenerator()
        container = build_container(generator)
        await container.stock_service.add(NewStockItem(name="courgettes", quantity=3, unit="piece"))
        liked = await container.recipe_service.create(recipe_content("Lomo", []), [], [], RecipeSource.SEED)
        await container.recipe_service.set_preference(liked.id, "Alex", None, True)

        # When
        await container.recipe_studio.draft_new("  ", None, False, True, TODAY, None, True)

        # Then
        context = generator.contexts[0]
        assert generator.requests == [DEFAULT_RECIPE_REQUEST]
        assert context.stock_only
        assert context.available_ingredients == ["courgettes"]
        assert context.member_tastes == ["Alex aime : Lomo"]
