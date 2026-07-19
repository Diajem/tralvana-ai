param(
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$Requirements = Join-Path $RepoRoot "services\api\requirements.txt"

if (-not (Test-Path $Python)) {
    Write-Host "Creating the Tralvana Python environment..."
    & python -m venv (Join-Path $RepoRoot ".venv")
    & $Python -m pip install -r $Requirements
}

$env:PYTHONPATH = "$RepoRoot;$RepoRoot\services\api"
$env:API_PORT = "$Port"

Push-Location $RepoRoot
try {
    Write-Host "Starting Tralvana API at http://localhost:$Port"
    Write-Host "Swagger: http://localhost:$Port/docs"
    & $Python -m uvicorn app.main:app --app-dir services/api --host 0.0.0.0 --port $Port --reload
}
finally {
    Pop-Location
}
