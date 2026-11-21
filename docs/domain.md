# Domaine

## Stock (`entities/_stock_item.py:StockItem`)

| Champ | Sens |
|---|---|
| `kind` | `ingredient` (cuisine, quantité suivie), `basique` (sel, huile, épices), `petit_dej_gouter` (céréales, biscuits, compotes, yaourts à boire, jus), `fruit`, `maison` (PQ, dentifrice, pastilles, croquettes…) |
| `channel` | Où l'acheter : `drive`, `marche` (défaut des fruits : jamais au drive), `autre` (ex. café, autre fournisseur) |
| `quantity` / `unit` | `None` = non suivi (seul le drapeau compte). Unités normalisées (`units.py`) : g, kg, ml, cl, l, piece… |
| `running_low` | Case « bientôt plus » : l'article part dans la liste à racheter |
| `expires_on` | Date limite ; « à finir vite » si ≤ `EXPIRING_SOON_DAYS` jours |

`needs_restock = running_low or quantity <= 0`. `restock()` (achat) remet `running_low` à faux, ajoute la quantité
convertie et garde la date la plus proche si du stock restait.

## Correspondance ingrédient ↔ stock (`availability.py`, `names.py`)

Noms normalisés (minuscules, sans accents, ligatures œ→oe, singulier, mots vides retirés).
Correspondance exacte d'abord, sinon l'article du stock doit contenir tous les mots de l'ingrédient
(« crème fraîche » trouve « crème fraîche épaisse », mais « pommes de terre » ne trouve pas « pommes »).

## Cuisiner (`use_cases/cooking_service.py`)

Portions → facteur `servings / recipe.servings`. Pour chaque ingrédient trouvé : décompte converti (jamais sous 0).
Résultat `CookLog` : `consumed` (restauré par l'annulation), `not_counted` (non suivi ou unité incompatible),
`missing` (absent du stock).

## Saisons (`entities/_recipe.py:Season`, `seasons.py`)

`Recipe.seasons` : `printemps`, `ete`, `automne`, `hiver`, plusieurs possibles ; liste vide = toute l'année.
`Recipe.fits(season)` est vrai si la liste est vide ou contient la saison. `season_of(day)` suit les saisons
météorologiques (déc.–fév. hiver, mars–mai printemps, juin–août été, sept.–nov. automne).
L'ancien tag `saison` est retiré à la lecture (`RecipeContent._drop_legacy_tags`).

## Suggestions (`suggestions.py:rank_recipes`)

Score = ratio d'ingrédients dispo × 100 + 15 par ingrédient à finir vite − 50 si cuisiné depuis moins de
`RECENTLY_COOKED_DAYS` jours + 12 si le membre aime + 8 s'il sait la faire (+10 « rapide » quand le filtre rapide est actif)
+ 10 si la recette est marquée pour la saison visée, − 30 si elle est marquée pour d'autres saisons
(saison visée = filtre `season`, sinon `season_of(today)` ; les recettes « toute l'année » sont neutres).
Le filtre `season` exclut les recettes qui ne lui correspondent pas.
Les desserts sont exclus sauf filtre `tag=dessert`. Constantes : `domain/constants.py`.

## Contexte de courses (`shopping.py:build_shopping_context`)

| Clé | Contenu |
|---|---|
| `to_buy_drive` / `to_buy_fresh_market` / `to_buy_other` | Articles à racheter, séparés par circuit, avec `preferred_product` |
| `expiring_soon`, `in_stock` | Garde-manger |
| `upcoming_plan` | Repas prévus (`UPCOMING_PLAN_DAYS`) et ingrédients manquants |
| `cooked_this_week`, `most_cooked_recently` | Ce que le foyer cuisine vraiment (semaine ISO en cours, 30 derniers jours) |
| `member_tastes` | Par membre : recettes qu'il sait faire, recettes qu'il aime |
| `preferred_products` | Produit le plus acheté par ingrédient (historique des courses) |
| `notes`, `guidance` | Mémoire du foyer + règles pour l'agent |
