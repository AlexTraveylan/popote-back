from datetime import date

import pytest
from faker import Faker

from src.container import Container
from src.domain.entities import RecipeContent, RecipeSource, Season
from src.domain.seasons import describe_seasons, season_of
from src.domain.suggestions import SuggestionCriteria
from tests.factories import FakeRecipeGenerator, build_container, recipe_content

fake = Faker("fr_FR")
WINTER_DAY = date(2026, 12, 15)


@pytest.mark.parametrize(
    ("day", "expected"),
    [
        (date(2026, 1, 10), Season.WINTER),
        (date(2026, 2, 28), Season.WINTER),
        (date(2026, 3, 1), Season.SPRING),
        (date(2026, 5, 31), Season.SPRING),
        (date(2026, 6, 1), Season.SUMMER),
        (date(2026, 8, 31), Season.SUMMER),
        (date(2026, 9, 1), Season.AUTUMN),
        (date(2026, 11, 30), Season.AUTUMN),
        (date(2026, 12, 1), Season.WINTER),
    ],
)
def test_season_of_follows_meteorological_seasons(day: date, expected: Season) -> None:
    # Given / When
    season = season_of(day)

    # Then
    assert season == expected


@pytest.mark.parametrize(
    ("seasons", "season", "fits"),
    [
        ([], Season.SUMMER, True),
        ([Season.SUMMER], Season.SUMMER, True),
        ([Season.SUMMER], Season.WINTER, False),
        ([Season.AUTUMN, Season.WINTER], Season.WINTER, True),
    ],
)
def test_recipe_fits_season(seasons: list[Season], season: Season, fits: bool) -> None:
    # Given
    content = recipe_content(fake.word(), [], seasons=seasons)

    # When / Then
    assert content.fits(season) is fits


def test_seasons_are_sorted_and_legacy_tag_is_dropped() -> None:
    # Given
    raw = {
        "title": fake.word(),
        "prep_minutes": 20,
        "ingredients": [],
        "steps": [],
        "tags": ["saison", "rapide"],
        "seasons": ["hiver", "printemps"],
    }

    # When
    content = RecipeContent.model_validate(raw)

    # Then
    assert content.tags == ["rapide"]
    assert content.seasons == [Season.SPRING, Season.WINTER]
    assert describe_seasons(content.seasons) == "printemps, hiver"
    assert describe_seasons([]) == "toute l'année"


async def _seasonal_container() -> Container:
    container = build_container()
    for title, seasons in (("Tarte tomate", [Season.SUMMER]), ("Pâtes", []), ("Raclette", [Season.WINTER])):
        await container.recipe_service.create(recipe_content(title, [], seasons=seasons), [], [], RecipeSource.SEED)
    return container


class TestSeasonalSuggestions:
    async def test_out_of_season_recipes_go_last_but_stay_available(self) -> None:
        # Given
        container = await _seasonal_container()

        # When
        suggestions = await container.suggestion_service.suggest(SuggestionCriteria(today=WINTER_DAY))

        # Then
        assert [suggestion.recipe.title for suggestion in suggestions] == ["Raclette", "Pâtes", "Tarte tomate"]
        assert "De saison (hiver)" in suggestions[0].reasons
        assert "Plutôt été" in suggestions[2].reasons

    async def test_explicit_season_filters_and_overrides_today(self) -> None:
        # Given
        container = await _seasonal_container()

        # When
        suggestions = await container.suggestion_service.suggest(
            SuggestionCriteria(today=WINTER_DAY, season=Season.SUMMER),
        )
        listed = await container.recipe_service.list_recipes(season=Season.SUMMER)

        # Then
        assert [suggestion.recipe.title for suggestion in suggestions] == ["Tarte tomate", "Pâtes"]
        assert [recipe.title for recipe in listed] == ["Pâtes", "Tarte tomate"]


class TestSeasonalGeneration:
    @pytest.mark.parametrize(
        ("requested", "expected"),
        [(None, Season.WINTER), (Season.SUMMER, Season.SUMMER)],
    )
    async def test_draft_targets_requested_or_current_season(
        self,
        requested: Season | None,
        expected: Season,
    ) -> None:
        # Given
        generator = FakeRecipeGenerator()
        container = build_container(generator)

        # When
        draft = await container.recipe_studio.draft_new(fake.sentence(), None, False, False, WINTER_DAY, requested)

        # Then
        assert generator.contexts[0].season == expected
        assert draft.seasons == [expected]
