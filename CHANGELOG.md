# Changelog

## 0.1.0 — 2026-11-21

- Première version : stock par familles (cuisine, basiques, petit-déj et goûters, fruits, maison) et par circuit
  d'achat (drive, marché, autre fournisseur), case « bientôt plus », dates limites.
- Recettes par membre (sait la faire / aime), tags (rapide, péruvien, poisson, végétarien…), CRUD.
- « J'ai cuisiné » : décompte du stock avec conversions d'unités et annulation.
- Suggestions du jour classées (disponibilité, ingrédients à finir vite, variété, goûts du membre).
- Génération et retouche de recettes avec OpenAI (`responses.parse`, sortie Pydantic).
- Serveur MCP : contexte de courses, enregistrement des courses avec réassort, historique d'achats, notes du foyer.
- Seed : 40 recettes, garde-manger de base ; seed privé local (non versionné).
