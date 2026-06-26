$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$backendDir = Join-Path $root "backend"
$uv = Get-Command "uv" -ErrorAction SilentlyContinue
$venvPython = Join-Path $backendDir ".venv\Scripts\python.exe"
$backendPort = 8010
$backendUrl = "http://127.0.0.1:$backendPort"

Write-Host "Iniciando backend en $backendUrl..." -ForegroundColor Cyan

try {
    $health = Invoke-RestMethod "$backendUrl/health" -TimeoutSec 2
    if ($health.status -eq "ok") {
        Write-Host "El backend ya está iniciado y responde correctamente." -ForegroundColor Green
        exit 0
    }
} catch {
    $listener = Get-NetTCPConnection -LocalPort $backendPort -State Listen -ErrorAction SilentlyContinue
    if ($listener) {
        throw "El puerto $backendPort está ocupado por el proceso $($listener.OwningProcess), pero no responde como AI Financial OS."
    }
}

Set-Location $backendDir

if ($uv) {
    & $uv.Source run uvicorn app.main:app --reload --port $backendPort
} elseif (Test-Path $venvPython) {
    & $venvPython -m uvicorn app.main:app --reload --port $backendPort
} else {
    throw "No se encontró uv ni backend\.venv. Ejecuta .\scripts\setup.ps1 primero."
}
