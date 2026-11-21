# Génération de recettes (ChatGPT)

Port `src/domain/ports/_recipe_generator.py:RecipeGenerator` (`create`, `rework`), contexte `GenerationContext`
construit par `use_cases/recipe_studio.py:RecipeStudio` : membres, membre demandeur, contrainte rapide,
saison visée (`season` de la demande, sinon `season_of(today)`),
ingrédients dispo (familles cuisine + basiques), ingrédients à finir vite, notes du foyer, titres existants.

Adapter `src/adapters/driven/recipe_generators/_openai.py:OpenAIRecipeGenerator` :
`AsyncOpenAI().responses.parse(model=OPENAI_MODEL, instructions=..., input=..., text_format=_GeneratedRecipe)`
→ `response.output_parsed` est une instance Pydantic validée (sortie structurée stricte : tous les champs
requis, `tags` limité à l'enum `RecipeTag`, `seasons` à l'enum `Season`). `None` ou `OpenAIError` → `RecipeGenerationError` (HTTP 502).

Les brouillons ne sont jamais enregistrés : le front les affiche dans le formulaire, l'utilisateur corrige puis
enregistre (`POST /api/recipes` avec `source=chatgpt`, ou `PUT /api/recipes/{id}` pour une retouche).

Sans `OPENAI_API_KEY` : `UnavailableRecipeGenerator` (HTTP 503), `recipe_generation_enabled=false` côté front.
