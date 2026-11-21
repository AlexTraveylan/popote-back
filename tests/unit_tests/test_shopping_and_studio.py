from datetime import date, timedelta

import pytest
from faker import Faker

from src.domain.entities import (
    MealSlot,
    PurchasedItem,
    RecipeSource,
    ShoppingChannel,
    ShoppingTrip,
    StockCategory,
    StockKind,
)
from src.domain.errors import DuplicateStockItemError
from src.use_cases.stock_service import NewStockItem
from tests.factories import FakeRecipeGenerator, build_container, recipe_content

fake = Faker("fr_FR")
TODAY = date(2026, 11, 21)


def _trip(items: list[PurchasedItem], shopped_on: date = TODAY) -> ShoppingTrip:
    return ShoppingTrip(store=fake.company(), shopped_on=shopped_on, items=items)


class TestShoppingService:
    async def test_record_trip_restocks_existing_and_creates_new_items(self) -> None:
        # Given
        container = build_container()
        await container.stock_service.add(NewStockItem(name="lardons", quantity=0, unit="g"))
        await container.stock_service.add(
            NewStockItem(name="papier toilette", kind=StockKind.HOUSEHOLD, running_low=True),
        )
        trip = _trip(
            [
                PurchasedItem(
                    product_name="AUCHAN Lardons nature 2x150g",
                    stock_name="Lardons",
                    packs=2,
                    pack_quantity=300,
                    pack_unit="g",
                    unit_price=2.76,
                ),
                PurchasedItem(
                    product_name="Papier toilette 12 rouleaux",
                    stock_name="papier toilette",
                    kind=StockKind.HOUSEHOLD,
                    unit_price=4.65,
                ),
                PurchasedItem(product_name="Potimarron 1 pièce", stock_name="potimarron", unit_price=2.49),
            ],
        )

        # When
        await container.shopping_service.record_trip(trip)
        stock = {item.name: item for item in await container.stock_service.list_items()}

        # Then
        assert stock["lardons"].quantity == 600
        assert not stock["papier toilette"].running_low
        assert stock["potimarron"].quantity == 1
        assert stock["potimarron"].unit == "piece"
        assert trip.computed_total == round(2.76 * 2 + 4.65 + 2.49, 2)

    async def test_context_separates_drive_market_and_other_suppliers(self) -> None:
        # Given
        container = build_container()
        await container.stock_service.add(NewStockItem(name="sel", kind=StockKind.STAPLE, running_low=True))
        await container.stock_service.add(NewStockItem(name="pommes", kind=StockKind.FRUIT, running_low=True))
        await container.stock_service.add(
            NewStockItem(
                name="café",
                kind=StockKind.BREAKFAST_SNACK,
                channel=ShoppingChannel.OTHER,
                running_low=True,
            ),
        )
        await container.stock_service.add(NewStockItem(name="compotes", kind=StockKind.BREAKFAST_SNACK))
        await container.shopping_service.record_trip(
            _trip([PurchasedItem(product_name="La Baleine sel fin", stock_name="sel", kind=StockKind.STAPLE)]),
            update_stock=False,
        )

        # When
        context = await container.shopping_service.context(TODAY)

        # Then
        assert [item.name for item in context.to_buy_drive] == ["sel"]
        assert context.to_buy_drive[0].preferred_product == "La Baleine sel fin"
        assert [item.name for item in context.to_buy_fresh_market] == ["pommes"]
        assert [item.name for item in context.to_buy_other] == ["café"]
        assert context.members == ["Alex", "Sam"]

    async def test_context_includes_week_history_plan_and_tastes(self) -> None:
        # Given
        container = build_container()
        recipe = await container.recipe_service.create(
            recipe_content("Lomo saltado", [("bœuf", 400, "g")]),
            ["Alex"],
            ["Sam"],
            RecipeSource.SEED,
        )
        await container.cooking_service.cook(recipe.id, "Alex", None, TODAY - timedelta(days=TODAY.weekday()))
        await container.cooking_service.cook(recipe.id, "Alex", None, TODAY - timedelta(days=20))
        await container.planning_service.plan(TODAY + timedelta(days=2), MealSlot.DINNER, recipe.id, "Alex")

        # When
        context = await container.shopping_service.context(TODAY)

        # Then
        assert [line.recipe_title for line in context.cooked_this_week] == ["Lomo saltado"]
        assert context.most_cooked_recently[0].times_cooked == 2
        assert context.upcoming_plan[0].missing == ["bœuf"]
        tastes = {taste.member: taste for taste in context.member_tastes}
        assert tastes["Alex"].can_cook == ["Lomo saltado"]
        assert tastes["Sam"].likes == ["Lomo saltado"]

    async def test_purchase_history_filters_by_ingredient(self) -> None:
        # Given
        container = build_container()
        await container.shopping_service.record_trip(
            _trip(
                [
                    PurchasedItem(product_name="HARRYS American Sandwich", stock_name="pain de mie"),
                    PurchasedItem(product_name="Comté AOP 350g", stock_name="comté", category=StockCategory.CREMERIE),
                ],
            ),
        )

        # When
        history = await container.shopping_service.purchase_history("pain de mie", 10)

        # Then
        assert [record.product_name for record in history] == ["HARRYS American Sandwich"]


class TestStockService:
    async def test_add_rejects_duplicates_by_normalized_name(self) -> None:
        # Given
        container = build_container()
        await container.stock_service.add(NewStockItem(name="Pommes de terre"))

        # When / Then
        with pytest.raises(DuplicateStockItemError):
            await container.stock_service.add(NewStockItem(name="pomme de terre"))


class TestRecipeStudio:
    async def test_draft_uses_available_stock_and_household_notes(self) -> None:
        # Given
        generator = FakeRecipeGenerator()
        container = build_container(generator)
        await container.stock_service.add(
            NewStockItem(name="courgettes", quantity=2, unit="piece", expires_on=TODAY + timedelta(days=1)),
        )
        await container.stock_service.add(NewStockItem(name="lessive", kind=StockKind.HOUSEHOLD))
        await container.note_service.add("Pas de choux de Bruxelles", "Alex")

        # When
        draft = await container.recipe_studio.draft_new("un plat de saison", "sam", True, True, TODAY)

        # Then
        context = generator.contexts[0]
        assert draft.title == "Idée : un plat de saison"
        assert context.available_ingredients == ["courgettes"]
        assert context.expiring_ingredients == ["courgettes"]
        assert context.household_notes == ["Pas de choux de Bruxelles"]
        assert context.member == "Sam"
        assert context.quick

    async def test_rework_returns_draft_without_saving(self) -> None:
        # Given
        container = build_container()
        recipe = await container.recipe_service.create(
            recipe_content("Quiche", [("œufs", 4, "piece")]),
            [],
            [],
            RecipeSource.MANUAL,
        )

        # When
        draft = await container.recipe_studio.draft_rework(recipe.id, "sans lardons", None, TODAY)

        # Then
        stored = await container.recipe_service.get(recipe.id)
        assert draft.title == "Quiche (sans lardons)"
        assert stored.title == "Quiche"
