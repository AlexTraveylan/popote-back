import pytest

from src.domain.names import names_match, normalize_name
from src.domain.units import convert, normalize_unit


class TestNames:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("Pommes de terre", "pomme terre"),
            ("Crème fraîche", "creme fraiche"),
            ("  ŒUFS ", "oeuf"),
            ("Bœuf à braiser", "boeuf braiser"),
            ("Huile d'olive", "huile olive"),
            ("Pâte d'ají amarillo", "pate aji amarillo"),
        ],
    )
    def test_normalize_name(self, raw: str, expected: str) -> None:
        # Given
        name = raw

        # When
        normalized = normalize_name(name)

        # Then
        assert normalized == expected

    @pytest.mark.parametrize(
        ("first", "second", "expected"),
        [
            ("crème fraîche", "Crème fraîche épaisse", True),
            ("pommes de terre", "pomme de terre", True),
            ("lardons", "lardons fumés", True),
            ("pommes de terre", "pommes", False),
            ("lardons fumés", "lardons", False),
            ("carottes", "patates douces", False),
            ("", "sel", False),
        ],
    )
    def test_names_match(self, first: str, second: str, expected: bool) -> None:
        # Given
        names = (first, second)

        # When
        result = names_match(*names)

        # Then
        assert result is expected


class TestUnits:
    @pytest.mark.parametrize(
        ("quantity", "source", "target", "expected"),
        [
            (1.5, "kg", "g", 1500.0),
            (250, "g", "kg", 0.25),
            (20, "cl", "ml", 200.0),
            (1, "L", "cl", 100.0),
            (3, "pièces", "piece", 3.0),
            (3, None, None, 3.0),
            (2, "g", "piece", None),
            (2, "kg", "l", None),
        ],
    )
    def test_convert(
        self,
        quantity: float,
        source: str | None,
        target: str | None,
        expected: float | None,
    ) -> None:
        # Given
        amount = quantity

        # When
        converted = convert(amount, source, target)

        # Then
        assert converted == expected

    def test_normalize_unit_ignores_blank(self) -> None:
        # Given
        unit = "   "

        # When
        normalized = normalize_unit(unit)

        # Then
        assert normalized is None
