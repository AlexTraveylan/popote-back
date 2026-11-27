# Architecture

Hexagonale, sur le modèle de hussard-machine_back.

```
main.py                         FastAPI : lifespan (init DB, seed, session MCP), CORS, routes /api, MCP monté sur /mcp
src/config.py                   Settings (pydantic-settings, .env)
src/container.py                Container : instancie repositories + services ; get_container / set_container / reset_container
src/domain/                     Pur : aucune dépendance aux adapters
  entities/                     StockItem, Recipe(+RecipeContent), CookLog, ShoppingTrip(+PurchasedItem), PlannedMeal, HouseholdNote
  ports/                        Interfaces ABC (repositories, RecipeGenerator)
  availability.py               Recette vs stock (find_stock_item, assess_recipe)
  suggestions.py                Classement des recettes du jour (rank_recipes)
  shopping.py                   Vue garde-manger et contexte de courses (build_pantry_overview, build_shopping_context)
  names.py / units.py           Normalisation des noms d'ingrédients, conversions g/kg, ml/cl/l
  household.py                  Membres du foyer (HOUSEHOLD_MEMBERS)
src/use_cases/                  Services applicatifs (orchestrent ports + domaine)
src/adapters/driving/http/      Routes FastAPI (/api), schémas de requête, mapping erreurs domaine -> HTTP
src/adapters/driving/mcp_server.py  Serveur MCP (MCPServer, SDK mcp 2.x)
src/adapters/driven/repositories/   Sql* (SQLModel) et InMemory* (tests)
src/adapters/driven/recipe_generators/  OpenAIRecipeGenerator, UnavailableRecipeGenerator
src/adapters/driven/seed/       Lecture des fichiers JSON de seed
```

## Ports et adapters

| Port (`src/domain/ports`) | Adapters |
|---|---|
| `StockRepository`, `RecipeRepository`, `CookLogRepository`, `ShoppingTripRepository`, `PlannedMealRepository`, `HouseholdNoteRepository` | `Sql*Repository` (prod), `InMemory*Repository` (tests) |
| `RecipeGenerator` | `OpenAIRecipeGenerator` (si `OPENAI_API_KEY`), `UnavailableRecipeGenerator` (sinon, 503) |

Trois sources de recettes = trois adapters « driving » vers le même `RecipeService` :

| Source | Entrée | `RecipeSource` |
|---|---|---|
| Formulaire du front | `POST /api/recipes` | `manuel` |
| ChatGPT | `POST /api/recipes/drafts` puis `POST /api/recipes` | `chatgpt` |
| Claude (conversation) | outil MCP `add_recipe` | `claude` |

## Persistance

`src/adapters/driven/db/models.py` : une table par agrégat, colonne `payload` JSON (entité Pydantic sérialisée)
+ colonnes indexées utiles aux requêtes (`name`, `title`, `cooked_on`, `shopped_on`, `planned_on`, `created_at`).
`_sql_document_store.py:SqlDocumentStore` factorise get/select/upsert/delete. SQLite par défaut
(`DATABASE_URL`), Postgres possible en changeant l'URL (`postgresql+asyncpg://…`, ajouter `asyncpg`).
Les tables sont créées au démarrage (`init_db`), pas de migrations pour l'instant.

## Services (`src/use_cases`)

| Service | Rôle |
|---|---|
| `StockService` | CRUD stock, drapeau « bientôt plus », vue garde-manger |
| `RecipeService` | CRUD recettes, goûts (fans = aime, dislikes = n'aime pas, suppression si tout le monde n'aime pas) |
| `CookingService` | « J'ai cuisiné » : décompte le stock (portions, unités), annulation qui restaure |
| `SuggestionService` | Recettes du jour classées |
| `RecipeStudio` | Brouillons ChatGPT (nouvelle recette, retouche) — jamais enregistrés automatiquement |
| `ShoppingService` | Enregistre une course (historique + réassort du stock), contexte de courses, historique d'achats |
| `PlanningService`, `NoteService` | Repas prévus, mémoire du foyer |
| `SeedDatabase` | Remplissage initial si aucune recette |
