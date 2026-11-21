from datetime import date, timedelta

from pydantic import BaseModel

from src.domain.availability import RecipeAvailability, assess_recipe
from src.domain.constants import (
    DEFAULT_SUGGESTION_LIMIT,
    RECENTLY_COOKED_DAYS,
    SCORE_AVAILABILITY_WEIGHT,
    SCORE_EXPIRING_BONUS,
    SCORE_MEMBER_COOK_BONUS,
    SCORE_MEMBER_FAN_BONUS,
    SCORE_QUICK_BONUS,
    SCORE_RECENTLY_COOKED_PENALTY,
)
from src.domain.entities import CookLog, Recipe, RecipeTag, StockItem


class SuggestionCriteria(BaseModel):
    today: date
    member: str | None = None
    quick_only: bool = False
    only_member_recipes: bool = False
    tag: RecipeTag | None = None
    limit: int = DEFAULT_SUGGESTION_LIMIT


class Suggestion(BaseModel):
    recipe: Recipe
    availability: RecipeAvailability
    score: float
    reasons: list[str]


def _last_cooked_on(recipe: Recipe, logs: list[CookLog]) -> date | None:
    dates = [log.cooked_on for log in logs if log.recipe_id == recipe.id]
    return max(dates) if dates else None


def _is_eligible(recipe: Recipe, criteria: SuggestionCriteria) -> bool:
    if criteria.tag is not None and criteria.tag not in recipe.tags:
        return False
    if criteria.tag is None and RecipeTag.DESSERT in recipe.tags:
        return False
    if criteria.quick_only and not recipe.is_quick:
        return False
    return not (criteria.only_member_recipes and criteria.member is not None and not recipe.concerns(criteria.member))


def _availability_reasons(availability: RecipeAvailability) -> tuple[float, list[str]]:
    score = availability.ratio * SCORE_AVAILABILITY_WEIGHT
    reasons: list[str] = []
    if not availability.missing:
        reasons.append("Tout est à la maison")
    else:
        reasons.append(f"Manque : {', '.join(availability.missing)}")
    if availability.expiring:
        score += SCORE_EXPIRING_BONUS * len(availability.expiring)
        reasons.append(f"Utilise vite : {', '.join(availability.expiring)}")
    return score, reasons


def _history_reasons(
    recipe: Recipe,
    logs: list[CookLog],
    today: date,
) -> tuple[float, list[str]]:
    last = _last_cooked_on(recipe, logs)
    if last is None or today - last > timedelta(days=RECENTLY_COOKED_DAYS):
        return 0.0, []
    days = (today - last).days
    label = "aujourd'hui" if days == 0 else f"il y a {days} j"
    return -SCORE_RECENTLY_COOKED_PENALTY, [f"Déjà cuisiné {label}"]


def _member_reasons(recipe: Recipe, criteria: SuggestionCriteria) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []
    if recipe.is_quick:
        score += SCORE_QUICK_BONUS if criteria.quick_only else 0.0
        reasons.append(f"Rapide ({recipe.prep_minutes} min)")
    if criteria.member is None:
        return score, reasons
    if criteria.member in recipe.fans:
        score += SCORE_MEMBER_FAN_BONUS
        reasons.append(f"{criteria.member} aime")
    if criteria.member in recipe.cooks:
        score += SCORE_MEMBER_COOK_BONUS
        reasons.append(f"{criteria.member} sait la faire")
    return score, reasons


def _suggest(
    recipe: Recipe,
    stock: list[StockItem],
    logs: list[CookLog],
    criteria: SuggestionCriteria,
) -> Suggestion:
    availability = assess_recipe(recipe, stock, criteria.today)
    parts = [
        _availability_reasons(availability),
        _history_reasons(recipe, logs, criteria.today),
        _member_reasons(recipe, criteria),
    ]
    return Suggestion(
        recipe=recipe,
        availability=availability,
        score=round(sum(score for score, _ in parts), 2),
        reasons=[reason for _, reasons in parts for reason in reasons],
    )


def rank_recipes(
    recipes: list[Recipe],
    stock: list[StockItem],
    logs: list[CookLog],
    criteria: SuggestionCriteria,
) -> list[Suggestion]:
    suggestions = [_suggest(recipe, stock, logs, criteria) for recipe in recipes if _is_eligible(recipe, criteria)]
    suggestions.sort(key=lambda suggestion: (-suggestion.score, suggestion.recipe.title))
    return suggestions[: criteria.limit]
