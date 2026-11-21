from datetime import date, timedelta

import pytest
from faker import Faker

from src.domain.entities import ShoppingChannel, StockItem, StockKind, default_channel

fake = Faker("fr_FR")
TODAY = date(2026, 11, 21)


class TestStockItem:
    def test_consume_converts_units_and_never_goes_negative(self) -> None:
        # Given
        item = StockItem(name=fake.word(), quantity=0.5, unit="kg")

        # When
        consumed = item.consume(800, "g")

        # Then
        assert consumed == 0.5
        assert item.quantity == 0
        assert item.is_out
        assert item.needs_restock

    def test_consume_untracked_staple_counts_nothing(self) -> None:
        # Given
        item = StockItem(name="sel", kind=StockKind.STAPLE)

        # When
        consumed = item.consume(1, "pincée")

        # Then
        assert consumed is None
        assert item.is_available

    def test_restock_clears_running_low_and_keeps_earliest_expiry(self) -> None:
        # Given
        item = StockItem(name="lardons", quantity=150, unit="g", expires_on=TODAY, running_low=True)

        # When
        item.restock(300, "g", TODAY + timedelta(days=10))

        # Then
        assert item.quantity == 450
        assert item.expires_on == TODAY
        assert not item.running_low

    def test_restock_after_empty_takes_new_expiry(self) -> None:
        # Given
        item = StockItem(name="saumon", quantity=0, unit="g", expires_on=TODAY - timedelta(days=5))

        # When
        item.restock(500, "g", TODAY + timedelta(days=2))

        # Then
        assert item.quantity == 500
        assert item.expires_on == TODAY + timedelta(days=2)

    @pytest.mark.parametrize(
        ("days_left", "expected"),
        [(0, True), (3, True), (4, False)],
    )
    def test_expires_within(self, days_left: int, expected: bool) -> None:
        # Given
        item = StockItem(name=fake.word(), quantity=1, unit="piece", expires_on=TODAY + timedelta(days=days_left))

        # When
        expiring = item.expires_within(TODAY, 3)

        # Then
        assert expiring is expected

    @pytest.mark.parametrize(
        ("kind", "channel"),
        [
            (StockKind.FRUIT, ShoppingChannel.FRESH_MARKET),
            (StockKind.INGREDIENT, ShoppingChannel.DRIVE),
            (StockKind.BREAKFAST_SNACK, ShoppingChannel.DRIVE),
            (StockKind.HOUSEHOLD, ShoppingChannel.DRIVE),
        ],
    )
    def test_default_channel(self, kind: StockKind, channel: ShoppingChannel) -> None:
        # Given
        stock_kind = kind

        # When
        result = default_channel(stock_kind)

        # Then
        assert result is channel
