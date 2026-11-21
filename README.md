# Popote — back-end

Gestion de la cuisine d'un foyer : stock (frigo, basiques, petit-déj et goûters, fruits, consommables de la maison),
recettes par membre, « j'ai cuisiné » qui décompte le stock, suggestions du jour, planning, historique des courses.
Tout est exposé en **API HTTP** pour le front [popote-front](https://github.com/AlexTraveylan/popote-front) et en
**serveur MCP** pour qu'un Claude prépare et passe les courses (drive) avec tout le contexte du foyer.

- Python 3.14 · FastAPI · SQLModel + SQLite · architecture hexagonale (ports / adapters)
- Génération et retouche de recettes avec ChatGPT via `responses.parse` et une sortie Pydantic garantie
- Serveur MCP (SDK `mcp` 2.x) monté sur `/mcp`
- Outillage : uv, ruff, ty, pytest, prek

## Démarrage (Windows)

Prérequis : [uv](https://docs.astral.sh/uv/) et Node 24+ (`winget install astral-sh.uv OpenJS.NodeJS`).

```powershell
git clone https://github.com/AlexTraveylan/popote-back
git clone https://github.com/AlexTraveylan/popote-front
cd popote-back
copy .env.example .env      # renseigner HOUSEHOLD_MEMBERS et, si voulu, OPENAI_API_KEY
.\scripts\start.ps1         # lance l'API (8000) et le front (5173), affiche l'adresse pour le téléphone
```

Le téléphone (même Wi-Fi) ouvre `http://<ip-du-pc>:5173` ; chacun choisit qui il est, le choix reste dans le
navigateur. Au premier accès réseau, Windows demande d'autoriser Node.js sur les réseaux privés.

## Claude et le MCP

```powershell
claude mcp add --transport http popote http://localhost:8000/mcp
```

Puis : « Prépare les courses de la semaine sur le drive avec Popote ». Détails et outils : [docs/mcp.md](docs/mcp.md).

## Développement

Voir [CLAUDE.md](CLAUDE.md) (commandes, conventions) et [docs/](docs/index.md) (architecture, domaine, API, MCP).

```powershell
.\scripts\validate.ps1      # ruff, ty, pytest
```
