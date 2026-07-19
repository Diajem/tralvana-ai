param(
    [int]$WebPort = 3001,
    [int]$ApiPort = 8000
)

$ErrorActionPreference = "Stop"
$PowerShell = (Get-Process -Id $PID).Path
$ApiScript = Join-Path $PSScriptRoot "start-api.ps1"
$WebScript = Join-Path $PSScriptRoot "start-web.ps1"

Start-Process $PowerShell -ArgumentList @("-NoExit", "-File", $ApiScript, "-Port", $ApiPort)
Start-Process $PowerShell -ArgumentList @("-NoExit", "-File", $WebScript, "-Port", $WebPort)

Write-Host "Tralvana is starting in two PowerShell windows."
Write-Host "Web:     http://localhost:$WebPort"
Write-Host "API:     http://localhost:$ApiPort"
Write-Host "Swagger: http://localhost:$ApiPort/docs"
