$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

if (-not $env:DATABASE_URL) {
    throw "DATABASE_URL is required. Copy .env.example to .env or set it in this shell."
}

python -m alembic -c services/api/alembic.ini upgrade head
