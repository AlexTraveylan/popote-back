from collections import Counter, defaultdict
from datetime import date, timedelta
from typing import Final

from pydantic import BaseModel

from src.domain.availability import assess_recipe
from src.domain.constants import EXPIRING_SOON_DAYS, FAVORITE_PRODUCTS_LIMIT, RECENT_TRIPS_LIMIT
from src.domain.entities import (
    CookLog,
    HouseholdNote,
    MealSlot,
    PlannedMeal,
    Recipe,
    ShoppingChannel,
    ShoppingTrip,
    StockCategory,
    StockItem,
    StockKind,
)
from src.domain.names import normalize_name

SHOPPING_GUIDANCE: Final = [
    "Ne mets dans le panier du drive que les articles de to_buy_drive, plus ce qu'il faut pour les recettes prévues.",
    "Les articles de to_buy_fresh_market (fruits frais) ne s'achètent jamais au drive : liste-les à part.",
    "Les articles de to_buy_other viennent d'un autre fournisseur : ne les ajoute pas au panier.",
    "Privilégie preferred_products (les produits déjà achetés) avant de chercher d'autres références.",
    "Après la commande, appelle record_shopping_trip avec les produits réellement mis au panier.",
]


class StockLine(BaseModel):
    name: str
    kind: StockKind
    category: StockCategory
    channel: ShoppingChannel
    quantity: float | None
    unit: str | None
    expires_on: date | None
    running_low: bool


class ToBuyItem(BaseModel):
    name: str
    kind: StockKind
    category: StockCategory
    channel: ShoppingChannel
    reason: str
    preferred_product: str | None = None


class PreferredProduct(BaseModel):
    stock_name: str
    product_name: str
    times_bought: int
    last_unit_price: float | None
    last_bought_on: date
    channel: ShoppingChannel


class PantryOverview(BaseModel):
    generated_on: date
    to_buy_drive: list[ToBuyItem]
    to_buy_fresh_market: list[ToBuyItem]
    to_buy_other: list[ToBuyItem]
    expiring_soon: list[StockLine]
    in_stock: list[StockLine]


class PlannedMealNeed(BaseModel):
    planned_on: date
    slot: MealSlot
    recipe_title: str
    cook: str | None
    missing: list[str]


class CookedMealLine(BaseModel):
    cooked_on: date
    recipe_title: str
    cooked_by: str


class RecipeFrequency(BaseModel):
    recipe_title: str
    times_cooked: int
    last_cooked_on: date


class MemberTaste(BaseModel):
    member: str
    can_cook: list[str]
    likes: list[str]
    dislikes: list[str]


class TripSummary(BaseModel):
    shopped_on: date
    store: str
    channel: ShoppingChannel
    total: float | None
    items_count: int


class ShoppingContext(PantryOverview):
    members: list[str]
    notes: list[str]
    guidance: list[str]
    upcoming_plan: list[PlannedMealNeed]
    cooked_this_week: list[CookedMealLine]
    most_cooked_recently: list[RecipeFrequency]
    member_tastes: list[MemberTaste]
    preferred_products: list[PreferredProduct]
    recent_trips: list[TripSummary]


def _stock_line(item: StockItem) -> StockLine:
    return StockLine(
        name=item.name,
        kind=item.kind,
        category=item.category,
        channel=item.channel,
        quantity=item.quantity,
        unit=item.unit,
        expires_on=item.expires_on,
        running_low=item.running_low,
    )


def preferred_products(trips: list[ShoppingTrip]) -> list[PreferredProduct]:
    counters: dict[str, Counter[str]] = defaultdict(Counter)
    latest: dict[tuple[str, str], tuple[date, float | None, ShoppingChannel, str]] = {}
    for trip in sorted(trips, key=lambda current: current.shopped_on):
        for item in trip.items:
            key = normalize_name(item.stock_name)
            counters[key][item.product_name] += 1
            latest[key, item.product_name] = (trip.shopped_on, item.unit_price, trip.channel, item.stock_name)
    products: list[PreferredProduct] = []
    for key, counter in counters.items():
        product_name, times = counter.most_common(1)[0]
        bought_on, price, channel, stock_name = latest[key, product_name]
        products.append(
            PreferredProduct(
                stock_name=stock_name,
                product_name=product_name,
                times_bought=times,
                last_unit_price=price,
                last_bought_on=bought_on,
                channel=channel,
            ),
        )
    products.sort(key=lambda product: (-product.times_bought, product.stock_name))
    return products[:FAVORITE_PRODUCTS_LIMIT]


def _to_buy(item: StockItem, products: dict[str, str]) -> ToBuyItem:
    return ToBuyItem(
        name=item.name,
        kind=item.kind,
        category=item.category,
        channel=item.channel,
        reason="épuisé" if item.is_out else "bientôt fini",
        preferred_product=products.get(item.key),
    )


def build_pantry_overview(
    stock: list[StockItem],
    trips: list[ShoppingTrip],
    today: date,
) -> PantryOverview:
    products = {normalize_name(product.stock_name): product.product_name for product in preferred_products(trips)}
    ordered = sorted(stock, key=lambda item: (item.kind, item.category, item.name.lower()))
    to_buy = [_to_buy(item, products) for item in ordered if item.needs_restock]
    return PantryOverview(
        generated_on=today,
        to_buy_drive=[item for item in to_buy if item.channel is ShoppingChannel.DRIVE],
        to_buy_fresh_market=[item for item in to_buy if item.channel is ShoppingChannel.FRESH_MARKET],
        to_buy_other=[item for item in to_buy if item.channel is ShoppingChannel.OTHER],
        expiring_soon=[_stock_line(item) for item in ordered if item.expires_within(today, EXPIRING_SOON_DAYS)],
        in_stock=[_stock_line(item) for item in ordered if item.is_available],
    )


def week_start(today: date) -> date:
    return today - timedelta(days=today.weekday())


def _recipe_frequencies(logs: list[CookLog]) -> list[RecipeFrequency]:
    grouped: dict[str, list[date]] = defaultdict(list)
    for log in logs:
        grouped[log.recipe_title].append(log.cooked_on)
    frequencies = [
        RecipeFrequency(recipe_title=title, times_cooked=len(dates), last_cooked_on=max(dates))
        for title, dates in grouped.items()
    ]
    frequencies.sort(key=lambda frequency: (-frequency.times_cooked, frequency.recipe_title))
    return frequencies


def _plan_needs(
    plan: list[PlannedMeal],
    recipes: dict[str, Recipe],
    stock: list[StockItem],
    today: date,
) -> list[PlannedMealNeed]:
    needs: list[PlannedMealNeed] = []
    for meal in sorted(plan, key=lambda current: (current.planned_on, current.slot)):
        recipe = recipes.get(str(meal.recipe_id))
        if recipe is None:
            continue
        needs.append(
            PlannedMealNeed(
                planned_on=meal.planned_on,
                slot=meal.slot,
                recipe_title=recipe.title,
                cook=meal.cook,
                missing=assess_recipe(recipe, stock, today).missing,
            ),
        )
    return needs


def _member_tastes(members: list[str], recipes: list[Recipe]) -> list[MemberTaste]:
    return [
        MemberTaste(
            member=member,
            can_cook=sorted(recipe.title for recipe in recipes if member in recipe.cooks),
            likes=sorted(recipe.title for recipe in recipes if member in recipe.fans),
            dislikes=sorted(recipe.title for recipe in recipes if member in recipe.dislikes),
        )
        for member in members
    ]


def _trip_summaries(trips: list[ShoppingTrip]) -> list[TripSummary]:
    recent = sorted(trips, key=lambda trip: trip.shopped_on, reverse=True)[:RECENT_TRIPS_LIMIT]
    return [
        TripSummary(
            shopped_on=trip.shopped_on,
            store=trip.store,
            channel=trip.channel,
            total=trip.computed_total,
            items_count=len(trip.items),
        )
        for trip in recent
    ]


def build_shopping_context(
    *,
    members: list[str],
    stock: list[StockItem],
    recipes: list[Recipe],
    recent_logs: list[CookLog],
    plan: list[PlannedMeal],
    trips: list[ShoppingTrip],
    notes: list[HouseholdNote],
    today: date,
) -> ShoppingContext:
    overview = build_pantry_overview(stock, trips, today)
    monday = week_start(today)
    return ShoppingContext(
        **overview.model_dump(),
        members=members,
        notes=[note.text for note in notes],
        guidance=SHOPPING_GUIDANCE,
        upcoming_plan=_plan_needs(plan, {str(recipe.id): recipe for recipe in recipes}, stock, today),
        cooked_this_week=[
            CookedMealLine(cooked_on=log.cooked_on, recipe_title=log.recipe_title, cooked_by=log.cooked_by)
            for log in sorted(recent_logs, key=lambda current: current.cooked_on)
            if log.cooked_on >= monday
        ],
        most_cooked_recently=_recipe_frequencies(recent_logs),
        member_tastes=_member_tastes(members, recipes),
        preferred_products=preferred_products(trips),
        recent_trips=_trip_summaries(trips),
    )
