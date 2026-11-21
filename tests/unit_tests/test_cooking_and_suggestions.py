from datetime import date, timedelta
from typing import Any

import pytest

from src.container import Container
from src.domain.entities import RecipeSource, RecipeTag, StockKind
from src.domain.errors import UnknownMemberError
from src.domain.suggestions import SuggestionCriteria
from src.use_cases.stock_service import NewStockItem
from tests.factories import build_container, recipe_content

TODAY = date(2026, 11, 21)


async def _stock(
    container: Container,
    name: str,
    quantity: float | None,
    unit: str | None,
    **extra: Any,
) -> None:
    await container.stock_service.add(NewStockItem(name=name, quantity=quantity, unit=unit, **extra))


class TestCookingService:
    async def test_cook_consumes_stock_scaled_to_servings_and_undo_restores_it(self) -> None:
        # Given
        container = build_container()
        await _stock(container, "Pâtes", 500, "g")
        await _stock(container, "Lardons", 300, "g")
        await _stock(container, "sel", None, None, kind=StockKind.STAPLE)
        recipe = await container.recipe_service.create(
            recipe_content("Pâtes lardons", [("pâtes", 400, "g"), ("lardons", 150, "g"), ("sel", None, None)]),
            ["Sam"],
            [],
            RecipeSource.MANUAL,
        )

        # When
        log = await container.cooking_service.cook(recipe.id, "sam", 2, TODAY)
        after_cooking = {item.name: item.quantity for item in await container.stock_service.list_items()}
        await container.cooking_service.undo(log.id)
        after_undo = {item.name: item.quantity for item in await container.stock_service.list_items()}

        # Then
        assert log.cooked_by == "Sam"
        assert after_cooking["Pâtes"] == 300
        assert after_cooking["Lardons"] == 225
        assert log.not_counted == ["sel"]
        assert after_undo["Pâtes"] == 500
        assert after_undo["Lardons"] == 300
        assert await container.cooking_service.history(TODAY, TODAY) == []

    async def test_cook_reports_missing_ingredients(self) -> None:
        # Given
        container = build_container()
        recipe = await container.recipe_service.create(
            recipe_content("Omelette", [("œufs", 6, "piece")]),
            [],
            [],
            RecipeSource.MANUAL,
        )

        # When
        log = await container.cooking_service.cook(recipe.id, "Alex", None, TODAY)

        # Then
        assert log.missing == ["œufs"]
        assert log.servings == 4

    async def test_cook_rejects_unknown_member(self) -> None:
        # Given
        container = build_container()
        recipe = await container.recipe_service.create(
            recipe_content("Omelette", [("œufs", 6, "piece")]),
            [],
            [],
            RecipeSource.MANUAL,
        )

        # When / Then
        with pytest.raises(UnknownMemberError):
            await container.cooking_service.cook(recipe.id, "Inconnu", None, TODAY)


class TestSuggestions:
    async def test_ranks_available_and_expiring_first_and_penalizes_recent(self) -> None:
        # Given
        container = build_container()
        await _stock(container, "colin", 600, "g", expires_on=TODAY + timedelta(days=1))
        await _stock(container, "pommes de terre", 2, "kg")
        fish = await container.recipe_service.create(
            recipe_content("Colin vapeur", [("colin", 600, "g"), ("pommes de terre", 800, "g")]),
            [],
            ["Sam"],
            RecipeSource.SEED,
        )
        beef = await container.recipe_service.create(
            recipe_content("Bœuf soja", [("bœuf", 400, "g"), ("pommes de terre", 500, "g")]),
            ["Sam"],
            [],
            RecipeSource.SEED,
        )
        omelette = await container.recipe_service.create(
            recipe_content("Purée", [("pommes de terre", 1, "kg")]),
            [],
            [],
            RecipeSource.SEED,
        )
        await container.cooking_service.cook(omelette.id, "Alex", None, TODAY - timedelta(days=1))

        # When
        suggestions = await container.suggestion_service.suggest(SuggestionCriteria(today=TODAY, member="Sam"))

        # Then
        titles = [suggestion.recipe.title for suggestion in suggestions]
        assert titles[0] == fish.title
        assert titles.index(beef.title) < titles.index(omelette.title)
        assert any("Utilise vite" in reason for reason in suggestions[0].reasons)

    async def test_filters_quick_member_and_desserts(self) -> None:
        # Given
        container = build_container()
        await container.recipe_service.create(
            recipe_content("Mijoté", [("bœuf", 800, "g")], prep_minutes=150),
            ["Sam"],
            [],
            RecipeSource.SEED,
        )
        await container.recipe_service.create(
            recipe_content("Gâteau", [("farine", 250, "g")], prep_minutes=20, tags=[RecipeTag.DESSERT]),
            ["Sam"],
            [],
            RecipeSource.SEED,
        )
        quick = await container.recipe_service.create(
            recipe_content("Express", [("pâtes", 400, "g")], prep_minutes=20),
            ["Sam"],
            [],
            RecipeSource.SEED,
        )
        await container.recipe_service.create(
            recipe_content("Express de Alex", [("riz", 300, "g")], prep_minutes=15),
            ["Alex"],
            [],
            RecipeSource.SEED,
        )

        # When
        suggestions = await container.suggestion_service.suggest(
            SuggestionCriteria(today=TODAY, member="Sam", quick_only=True, only_member_recipes=True),
        )

        # Then
        assert [suggestion.recipe.title for suggestion in suggestions] == [quick.title]
