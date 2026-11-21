$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

Write-Host "Ruff (lint)..."
uv run ruff check . --fix
if ($LASTEXITCODE) { exit $LASTEXITCODE }

Write-Host "Ruff (format)..."
uv run ruff format .
if ($LASTEXITCODE) { exit $LASTEXITCODE }

Write-Host "Ty (types)..."
uv run ty check .
if ($LASTEXITCODE) { exit $LASTEXITCODE }

Write-Host "Pytest..."
uv run pytest -q
if ($LASTEXITCODE) { exit $LASTEXITCODE }

Write-Host "Tout est vert."
