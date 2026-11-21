from collections.abc import Callable
from datetime import date, timedelta
from typing import Final
from uuid import UUID

from mcp.server.mcpserver import MCPServer
from pydantic import BaseModel

from src.container import Container
from src.domain.entities import (
    CookLog,
    HouseholdNote,
    MealSlot,
    PlannedMeal,
    PurchasedItem,
    Recipe,
    RecipeContent,
    RecipeSource,
    RecipeTag,
    Season,
    ShoppingChannel,
    ShoppingTrip,
    StockItem,
)
from src.domain.shopping import PantryOverview, ShoppingContext
from src.use_cases.shopping_service import PurchaseRecord
from src.use_cases.stock_service import NewStockItem, StockItemPatch

INSTRUCTIONS: Final = """Popote gère la cuisine d'un foyer : stock, recettes, repas cuisinés et historique des courses.
Avant de faire les courses : appelle get_shopping_context. Il contient ce qui manque (to_buy_drive, to_buy_fresh_market,
to_buy_other), les produits bientôt périmés, les repas prévus et leurs ingrédients manquants, ce que le foyer a vraiment
cuisiné cette semaine et ces 30 derniers jours, les goûts de chacun, les notes du foyer et les produits préférés déjà achetés.
Règles : les fruits frais (to_buy_fresh_market) ne s'achètent pas au drive ; to_buy_other vient d'un autre fournisseur.
Après la commande : appelle record_shopping_trip avec les produits réellement mis au panier (stock_name = nom générique
de l'ingrédient, product_name = libellé exact du magasin). Le stock se met à jour tout seul.
Quand une recette est discutée avec l'utilisateur, ajoute-la avec add_recipe (noms d'ingrédients génériques)."""


class RecipeOverview(BaseModel):
    id: UUID
    title: str
    prep_minutes: int
    is_quick: bool
    tags: list[RecipeTag]
    seasons: list[Season]
    cooks: list[str]
    fans: list[str]
    ingredients: list[str]


class TripRecorded(BaseModel):
    trip_id: UUID
    items_count: int
    total: float | None


def _overview(recipe: Recipe) -> RecipeOverview:
    return RecipeOverview(
        id=recipe.id,
        title=recipe.title,
        prep_minutes=recipe.prep_minutes,
        is_quick=recipe.is_quick,
        tags=recipe.tags,
        seasons=recipe.seasons,
        cooks=recipe.cooks,
        fans=recipe.fans,
        ingredients=[ingredient.name for ingredient in recipe.ingredients],
    )


def _today() -> date:
    return date.today()  # noqa: DTZ011


def build_mcp_server(container_provider: Callable[[], Container]) -> MCPServer:
    server = MCPServer(name="popote", title="Popote", instructions=INSTRUCTIONS)

    @server.tool(
        description="Tout le contexte pour préparer les courses : manques, stock, périmés, repas prévus, habitudes et produits préférés."
    )
    async def get_shopping_context() -> ShoppingContext:
        return await container_provider().shopping_service.context(_today())

    @server.tool(
        description="Ingrédients encore disponibles et articles à racheter, séparés par circuit d'achat (drive, marché, autre)."
    )
    async def list_available_ingredients() -> PantryOverview:
        return await container_provider().stock_service.overview(_today())

    @server.tool(
        description=(
            "Liste les recettes du foyer, filtrables par membre (qui sait la faire ou l'aime), tag, rapidité et saison. "
            "seasons vide = recette de toute l'année ; le filtre season garde aussi ces recettes-là."
        )
    )
    async def list_recipes(
        member: str | None = None,
        tag: RecipeTag | None = None,
        quick_only: bool = False,
        season: Season | None = None,
    ) -> list[RecipeOverview]:
        recipes = await container_provider().recipe_service.list_recipes(member, tag, quick_only, season)
        return [_overview(recipe) for recipe in recipes]

    @server.tool(description="Recette complète : ingrédients avec quantités, étapes, tags, membres.")
    async def get_recipe(recipe_id: UUID) -> Recipe:
        return await container_provider().recipe_service.get(recipe_id)

    @server.tool(
        description="Ajoute une recette discutée avec l'utilisateur. cooks = qui sait la faire, fans = qui l'aime."
    )
    async def add_recipe(
        recipe: RecipeContent,
        cooks: list[str] | None = None,
        fans: list[str] | None = None,
    ) -> Recipe:
        return await container_provider().recipe_service.create(recipe, cooks or [], fans or [], RecipeSource.CLAUDE)

    @server.tool(description="Remplace le contenu d'une recette existante (titre, ingrédients, étapes, tags).")
    async def update_recipe(recipe_id: UUID, recipe: RecipeContent) -> Recipe:
        return await container_provider().recipe_service.replace_content(recipe_id, recipe)

    @server.tool(
        description="Enregistre des courses : historique des produits achetés et remise à jour automatique du stock."
    )
    async def record_shopping_trip(
        store: str,
        items: list[PurchasedItem],
        shopped_on: date | None = None,
        channel: ShoppingChannel = ShoppingChannel.DRIVE,
        total: float | None = None,
        notes: str = "",
    ) -> TripRecorded:
        trip = ShoppingTrip(
            store=store,
            channel=channel,
            shopped_on=shopped_on or _today(),
            items=items,
            total=total,
            notes=notes,
        )
        saved = await container_provider().shopping_service.record_trip(trip)
        return TripRecorded(trip_id=saved.id, items_count=len(saved.items), total=saved.computed_total)

    @server.tool(
        description="Produits achetés lors des courses précédentes, filtrables par ingrédient ou libellé (ex. « pain de mie »)."
    )
    async def get_purchase_history(query: str | None = None, limit: int = 50) -> list[PurchaseRecord]:
        return await container_provider().shopping_service.purchase_history(query, limit)

    @server.tool(description="Met à jour un article du stock par son nom, ou le crée s'il n'existe pas.")
    async def update_stock_item(
        name: str,
        quantity: float | None = None,
        unit: str | None = None,
        running_low: bool | None = None,
        expires_on: date | None = None,
    ) -> StockItem:
        service = container_provider().stock_service
        existing = await service.find_by_name(name)
        if existing is None:
            return await service.add(
                NewStockItem(name=name, quantity=quantity, unit=unit, expires_on=expires_on),
            )
        patch = StockItemPatch(quantity=quantity, unit=unit, running_low=running_low, expires_on=expires_on)
        return await service.update(existing.id, patch)

    @server.tool(description="Mémorise une préférence ou une habitude du foyer (ex. « pas de choux de Bruxelles »).")
    async def add_household_note(text: str, author: str | None = None) -> HouseholdNote:
        return await container_provider().note_service.add(text, author)

    @server.tool(description="Repas réellement cuisinés ces derniers jours, avec qui les a faits.")
    async def get_cooking_history(days: int = 30) -> list[CookLog]:
        return await container_provider().cooking_service.recent(_today(), days)

    @server.tool(description="Prévoit une recette pour un repas (petit_dej, midi, gouter, soir).")
    async def plan_meal(
        planned_on: date,
        slot: MealSlot,
        recipe_id: UUID,
        cook: str | None = None,
    ) -> PlannedMeal:
        return await container_provider().planning_service.plan(planned_on, slot, recipe_id, cook)

    @server.tool(description="Repas prévus à partir d'aujourd'hui.")
    async def list_planned_meals(days: int = 7) -> list[PlannedMeal]:
        today = _today()
        return await container_provider().planning_service.between(today, today + timedelta(days=days))

    return server
