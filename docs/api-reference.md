# API HTTP

Routes dans `src/adapters/driving/http/routes.py`. OpenAPI interactif : `http://localhost:8000/docs`.
`on=YYYY-MM-DD` (facultatif) = jour de référence, défaut aujourd'hui. Erreurs : `{"detail": "..."}`
(404 introuvable, 400 membre inconnu, 409 doublon de stock, 503 ChatGPT non configuré, 502 erreur OpenAI).

| Méthode | Route | Rôle |
|---|---|---|
| GET | `/api/household` | Membres, énumérations, `recipe_generation_enabled` |
| GET | `/api/stock` | Tout le stock |
| GET | `/api/stock/overview?on=` | À racheter par circuit, à finir vite, en stock |
| POST | `/api/stock` | Ajouter un article (`NewStockItem`) |
| PATCH | `/api/stock/{id}` | Modifier (`StockItemPatch`, `clear_quantity`, `clear_expiry`) |
| PUT | `/api/stock/{id}/running-low` | Case « bientôt plus » |
| DELETE | `/api/stock/{id}` | Retirer |
| GET | `/api/recipes?member=&tag=&quick=` | Recettes |
| POST | `/api/recipes` | Créer (contenu + `cooks`, `fans`, `source`) |
| GET/PUT/DELETE | `/api/recipes/{id}` | Lire, remplacer le contenu, supprimer |
| PUT | `/api/recipes/{id}/members` | Remplacer `cooks` et `fans` |
| PUT | `/api/recipes/{id}/preferences` | `{member, can_cook?, likes?}` |
| GET | `/api/recipes/{id}/availability?on=` | Ingrédient par ingrédient vs stock |
| POST | `/api/recipes/drafts` | Brouillon ChatGPT `{request, member, quick, use_stock}` |
| POST | `/api/recipes/{id}/drafts` | Retouche ChatGPT `{instruction, member}` |
| POST | `/api/recipes/{id}/cook` | « J'ai cuisiné » `{member, servings?, cooked_on?}` → `CookLog` |
| GET | `/api/suggestions?on=&member=&quick=&mine=&tag=&limit=` | Recettes du jour classées |
| GET | `/api/cook-logs?start=&end=` · `/api/cook-logs/week?on=` | Repas cuisinés |
| DELETE | `/api/cook-logs/{id}` | Annuler (restaure le stock) |
| GET/POST | `/api/plan` · DELETE `/api/plan/{id}` | Planning |
| GET | `/api/shopping/context?on=` | Contexte complet de courses (identique au MCP) |
| GET/POST | `/api/shopping/trips` · DELETE `/api/shopping/trips/{id}` | Historique ; POST réassort le stock (`update_stock=false` pour l'historique seul) |
| GET | `/api/shopping/history?query=&limit=` | Produits achetés |
| GET/POST | `/api/notes` · DELETE `/api/notes/{id}` | Mémoire du foyer |
| GET | `/health` | Santé |
