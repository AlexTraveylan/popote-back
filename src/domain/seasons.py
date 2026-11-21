from datetime import date
from typing import Final

from src.domain.entities import Season

SEASON_LABELS: Final = {
    Season.SPRING: "printemps",
    Season.SUMMER: "été",
    Season.AUTUMN: "automne",
    Season.WINTER: "hiver",
}

_SEASONS_BY_QUARTER: Final = (Season.WINTER, Season.SPRING, Season.SUMMER, Season.AUTUMN)


def season_of(day: date) -> Season:
    return _SEASONS_BY_QUARTER[(day.month % 12) // 3]


def describe_seasons(seasons: list[Season]) -> str:
    if not seasons:
        return "toute l'année"
    return ", ".join(SEASON_LABELS[season] for season in seasons)
