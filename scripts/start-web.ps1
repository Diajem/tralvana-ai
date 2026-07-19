param(
    [int]$Port = 3001
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$WebRoot = Join-Path $RepoRoot "apps\web"

Push-Location $WebRoot
try {
    if (-not (Test-Path (Join-Path $WebRoot "node_modules"))) {
        Write-Host "Installing Tralvana frontend dependencies..."
        & npm ci
    }

    $env:NEXT_PUBLIC_API_URL = "http://localhost:8000"
    Write-Host "Starting Tralvana at http://localhost:$Port"
    & npm run dev -- --hostname 127.0.0.1 --port $Port
}
finally {
    Pop-Location
}
