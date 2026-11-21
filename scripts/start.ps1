param(
    [string]$FrontPath = (Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) "popote-front"),
    [int]$ApiPort = 8000,
    [int]$FrontPort = 5173
)

$ErrorActionPreference = "Stop"
$BackPath = Split-Path -Parent $PSScriptRoot
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

if (-not (Test-Path $FrontPath)) {
    throw "Front introuvable : $FrontPath (clone popote-front à côté de popote-back, ou passe -FrontPath)"
}

Set-Location $BackPath
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Fichier .env créé depuis .env.example : renseigne HOUSEHOLD_MEMBERS et OPENAI_API_KEY." -ForegroundColor Yellow
}
uv sync --quiet

Set-Location $FrontPath
if (-not (Test-Path "node_modules")) {
    npm install
}

$api = Start-Process -PassThru -NoNewWindow -WorkingDirectory $BackPath -FilePath "uv" `
    -ArgumentList "run", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "$ApiPort"

$lanAddresses = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" -and $_.InterfaceAlias -notmatch "vEthernet|WSL|Loopback" } |
    Select-Object -ExpandProperty IPAddress

Write-Host ""
Write-Host "Popote démarre :" -ForegroundColor Green
Write-Host "  Sur ce PC       : http://localhost:$FrontPort"
foreach ($address in $lanAddresses) {
    Write-Host "  Sur le téléphone: http://${address}:$FrontPort  (même Wi-Fi)"
}
Write-Host "  API (docs)      : http://localhost:$ApiPort/docs"
Write-Host "  MCP pour Claude : http://localhost:$ApiPort/mcp"
Write-Host "Ctrl+C pour tout arrêter."
Write-Host ""

$env:VITE_API_PROXY_TARGET = "http://127.0.0.1:$ApiPort"
try {
    npm run dev -- --port $FrontPort --strictPort
}
finally {
    if ($api -and -not $api.HasExited) {
        taskkill /PID $api.Id /T /F | Out-Null
    }
}
