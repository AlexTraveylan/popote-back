from typing import Final, override

from openai import AsyncOpenAI, OpenAIError
from pydantic import BaseModel

from src.domain.entities import RecipeContent, RecipeIngredient, RecipeTag, Season
from src.domain.errors import RecipeGenerationError
from src.domain.ports import GenerationContext, RecipeGenerator
from src.domain.seasons import SEASON_LABELS

_INSTRUCTIONS: Final = """Tu es le cuisinier d'un foyer français (deux adultes, deux enfants de 6 et 8 ans) avec une touche péruvienne.
Tu proposes des recettes familiales réalistes, en français, avec les produits de la saison visée.
Règles de sortie :
- Noms d'ingrédients courts et génériques, au pluriel courant, sans marque (ex. « pommes de terre », « crème fraîche », « lardons »), pour qu'ils correspondent au stock du foyer.
- Unités parmi : g, kg, ml, cl, l, piece, c. à s., c. à c., tranche, gousse, botte, pincée. quantity = null si sans objet (sel, poivre).
- optional = true pour les ingrédients de finition ou facultatifs (sel, poivre, herbes).
- servings = 4 par défaut. prep_minutes = temps total réel (préparation + cuisson).
- steps : 3 à 8 étapes courtes et concrètes.
- tags : uniquement parmi la liste autorisée ; « rapide » seulement si prep_minutes <= 30.
- seasons : saisons où la recette a du sens (printemps, ete, automne, hiver), plusieurs possibles ; liste vide si elle se fait toute l'année.
- Ne propose pas un titre déjà existant dans le foyer."""


class _GeneratedIngredient(BaseModel):
    name: str
    quantity: float | None
    unit: str | None
    optional: bool


class _GeneratedRecipe(BaseModel):
    title: str
    summary: str
    servings: int
    prep_minutes: int
    ingredients: list[_GeneratedIngredient]
    steps: list[str]
    tags: list[RecipeTag]
    seasons: list[Season]


def _describe_context(context: GenerationContext) -> str:
    lines = [f"Membres du foyer : {', '.join(context.members)}."]
    if context.member:
        lines.append(f"La recette est pour {context.member}, qui la cuisinera.")
    if context.quick:
        lines.append("Contrainte : recette rapide, 30 minutes maximum tout compris.")
    lines.append(f"Saison visée : {SEASON_LABELS[context.season]}.")
    if context.available_ingredients:
        lines.append(f"Ingrédients disponibles à utiliser en priorité : {', '.join(context.available_ingredients)}.")
    if context.expiring_ingredients:
        lines.append(f"À utiliser d'urgence (bientôt périmés) : {', '.join(context.expiring_ingredients)}.")
    if context.stock_only:
        lines.append(
            "Contrainte forte : n'utilise que les ingrédients disponibles listés, "
            "plus sel, poivre, huile et épices courantes. Rien d'autre à acheter."
        )
    if context.member_tastes:
        lines.append("Goûts connus (à respecter, sans refaire ces recettes) :")
        lines.extend(f"- {taste}" for taste in context.member_tastes)
    if context.household_notes:
        lines.append("Préférences du foyer :")
        lines.extend(f"- {note}" for note in context.household_notes)
    if context.existing_titles:
        lines.append(f"Recettes déjà connues (ne pas dupliquer) : {', '.join(context.existing_titles)}.")
    lines.append(f"Tags autorisés : {', '.join(tag.value for tag in RecipeTag)}.")
    return "\n".join(lines)


def _describe_recipe(recipe: RecipeContent) -> str:
    return recipe.model_dump_json(indent=2)


def _to_content(generated: _GeneratedRecipe) -> RecipeContent:
    return RecipeContent(
        title=generated.title,
        summary=generated.summary,
        servings=generated.servings,
        prep_minutes=generated.prep_minutes,
        ingredients=[
            RecipeIngredient(
                name=ingredient.name,
                quantity=ingredient.quantity,
                unit=ingredient.unit,
                optional=ingredient.optional,
            )
            for ingredient in generated.ingredients
        ],
        steps=generated.steps,
        tags=list(dict.fromkeys(generated.tags)),
        seasons=generated.seasons,
    )


class OpenAIRecipeGenerator(RecipeGenerator):
    def __init__(self, api_key: str, model: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def _parse(self, prompt: str) -> RecipeContent:
        try:
            response = await self._client.responses.parse(
                model=self._model,
                instructions=_INSTRUCTIONS,
                input=prompt,
                text_format=_GeneratedRecipe,
            )
        except OpenAIError as error:
            raise RecipeGenerationError(f"OpenAI a refusé la demande : {error}") from error
        parsed = response.output_parsed
        if parsed is None:
            raise RecipeGenerationError("OpenAI n'a pas renvoyé de recette exploitable")
        return _to_content(parsed)

    @override
    async def create(self, request: str, context: GenerationContext) -> RecipeContent:
        prompt = f"{_describe_context(context)}\n\nDemande : {request}"
        return await self._parse(prompt)

    @override
    async def rework(
        self,
        recipe: RecipeContent,
        instruction: str,
        context: GenerationContext,
    ) -> RecipeContent:
        prompt = (
            f"{_describe_context(context)}\n\nRecette actuelle :\n{_describe_recipe(recipe)}\n\n"
            f"Modifie cette recette selon la consigne suivante, en gardant tout le reste : {instruction}\n"
            "Tu peux garder le même titre s'il reste juste."
        )
        return await self._parse(prompt)
