# Données de départ

Chargées au démarrage par `SeedDatabase.seed_if_empty` uniquement si la base n'a aucune recette
(`SEED_ON_STARTUP=true`). Fichiers lus dans l'ordre de `SEED_FILES`, fusionnés (`SeedData.merged_with`).

| Fichier | Versionné | Contenu |
|---|---|---|
| `seed/recipes.json` | oui | ~40 recettes familiales (express, mijotés, péruviennes, végétariennes, desserts) |
| `seed/pantry.json` | oui | Basiques, petit-déj et goûters, fruits (circuit marché), consommables maison, café (autre fournisseur) |
| `data/private_seed.json` | **non** | `recipe_members` (qui sait faire / aime chaque recette), `notes` du foyer, `trips` (historique de courses réel) |

Format : `src/use_cases/seed_database.py:SeedData`. Les membres inconnus de `HOUSEHOLD_MEMBERS` sont ignorés.
Les courses du seed sont importées comme historique seulement (pas de réassort du stock).

Repartir de zéro : arrêter le serveur, supprimer `data/popote.db*`, relancer.
