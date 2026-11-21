# CLAUDE.md - popote-back

## Llm documentation

@docs/index.md

## Project Overview

Back-end de Popote : stock de la cuisine, recettes, repas cuisinés, planning et historique des courses d'un foyer.
Exposé en API HTTP (pour le front `popote-front`) et en serveur MCP (pour qu'un Claude fasse les courses).
Python 3.14, FastAPI, SQLModel sur SQLite, OpenAI Responses API, SDK MCP 2.x, architecture hexagonale.

## Commands

- Install dependencies: `uv sync`
- Run server: `uv run uvicorn main:app --reload`
- Run back + front: `.\scripts\start.ps1`
- Lint: `uv run ruff check . --fix`
- Format: `uv run ruff format .`
- Type check: `uv run ty check .`
- Test: `uv run pytest`
- Hooks: `uv run prek install` puis `uv run prek run --all-files`

## Code Style Rules

### Comments

- Code must be self-documenting. No comments except linter directives (`# noqa`, `# type: ignore`)
- If you need to explain code, extract it into a well-named function instead
- No docstrings (les descriptions des outils MCP passent par `@server.tool(description=...)`)

### Python

- Imports always at module top, never inside functions
- Use native Python types (`list`, `dict`, `tuple`, `| None`) instead of `typing` equivalents
- Use `Final` for constants, placed in `src/domain/constants.py`
- Multi-line parameters: if more than 2 params (excluding `self`), each on its own line with trailing comma
- Prefer pure functions when possible (`src/domain/*.py` ne dépend d'aucun adapter)
- Le domaine reçoit la date du jour en paramètre (`today: date`), jamais `date.today()`

### Tests (`**/test_*.py`)

- All test methods must have `-> None` return type annotation.
- Structure every test with `# Given`, `# When`, `# Then` comments.
- Use `Faker` (`fake = Faker()` at module level) for generating test data instead of hardcoded strings.
- Use `pytest.mark.parametrize` for exhaustive value coverage.
- Les services se testent avec `tests/factories.py:build_container` (repositories en mémoire, `FakeRecipeGenerator`).

## Validation

All checks must pass before committing:

```powershell
.\scripts\validate.ps1
```

## Données privées

`data/` est ignoré par git : base SQLite et `data/private_seed.json` (membres par recette, notes du foyer,
historique de courses). Ne jamais committer de données personnelles du foyer ; le seed public est dans `seed/`.

## docs/ maintenance protocol

After every change to the code, update /docs folder content

1. **What to update**: if you add/remove/move a port, an adapter, a route, an MCP tool or a business constant → update the relevant doc + the map in `docs/index.md`.
2. **Pointers**: prefer stable symbols (`file.py:ClassName`) over line numbers.
3. **Style**: dense, LLM-oriented. Tables and pointers to the code rather than long paraphrases.
4. **No duplication**: commands and conventions live in `CLAUDE.md`; link to it.

## Before push

- bump version with `uv version --bump <patch|minor|major>`
- add an entry in CHANGELOG.md
- check if doc need to be update using docs/index.md
