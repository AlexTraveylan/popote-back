# Serveur MCP

`src/adapters/driving/mcp_server.py:build_mcp_server` (SDK `mcp` 2.x, `MCPServer`). Monté dans FastAPI :
**`http://localhost:8000/mcp`**, transport streamable HTTP sans état, réponses JSON. Protection DNS rebinding :
hôtes autorisés `MCP_ALLOWED_HOSTS` (localhost par défaut). Pas d'authentification : réservé au PC local.

## Brancher Claude

Claude Code :

```powershell
claude mcp add --transport http popote http://localhost:8000/mcp
```

Claude Desktop (connecteur local via `mcp-remote`) dans `claude_desktop_config.json` :

```json
{ "mcpServers": { "popote": { "command": "npx", "args": ["-y", "mcp-remote", "http://localhost:8000/mcp"] } } }
```

## Outils

| Outil | Rôle |
|---|---|
| `get_shopping_context` | Tout pour préparer les courses (voir `domain.md`, contexte de courses) |
| `list_available_ingredients` | Ingrédients dispo + à racheter par circuit (drive, marché, autre) |
| `list_recipes(member?, tag?, quick_only?)` | Vue compacte des recettes |
| `get_recipe(recipe_id)` | Recette complète |
| `add_recipe(recipe, cooks?, fans?)` | Ajouter une recette discutée avec l'utilisateur (source `claude`) |
| `update_recipe(recipe_id, recipe)` | Remplacer le contenu |
| `record_shopping_trip(store, items, shopped_on?, channel?, total?, notes?)` | Historique + réassort automatique du stock |
| `get_purchase_history(query?, limit?)` | Produits achetés (ex. « pain de mie ») |
| `update_stock_item(name, quantity?, unit?, running_low?, expires_on?)` | Mettre à jour ou créer un article |
| `add_household_note(text, author?)` | Mémoriser une préférence |
| `get_cooking_history(days?)` | Repas réellement cuisinés |
| `plan_meal(...)`, `list_planned_meals(days?)` | Planning |

## Parcours « faire les courses »

1. `get_shopping_context` → manques par circuit, repas prévus et leurs manques, habitudes réelles, notes, produits préférés.
2. Remplir le panier du drive avec `to_buy_drive` + manques des repas prévus, en privilégiant `preferred_products`.
   Ne jamais ajouter `to_buy_fresh_market` (fruits frais, marché) ni `to_buy_other` (autre fournisseur).
3. Après validation du panier par l'utilisateur : `record_shopping_trip` avec, pour chaque ligne,
   `product_name` (libellé exact du magasin), `stock_name` (nom générique), `kind`, `category`, `packs`,
   `pack_quantity` + `pack_unit` quand c'est mesurable, `unit_price`, `expires_on` si connu.
