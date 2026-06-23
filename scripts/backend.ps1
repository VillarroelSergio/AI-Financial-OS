$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$backendDir = Join-Path $root "backend"
$uv = Get-Command "uv" -ErrorAction SilentlyContinue
$venvPython = Join-Path $backendDir ".venv\Scripts\python.exe"

Write-Host "Iniciando backend en http://127.0.0.1:8000..." -ForegroundColor Cyan

try {
    $health = Invoke-RestMethod "http://127.0.0.1:8000/health" -TimeoutSec 2
    if ($health.status -eq "ok") {
        Write-Host "El backend ya está iniciado y responde correctamente." -ForegroundColor Green
        exit 0
    }
} catch {
    $listener = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
    if ($listener) {
        throw "El puerto 8000 está ocupado por el proceso $($listener.OwningProcess), pero no responde como AI Financial OS."
    }
}

Set-Location $backendDir

if ($uv) {
    & $uv.Source run uvicorn app.main:app --reload --port 8000
} elseif (Test-Path $venvPython) {
    & $venvPython -m uvicorn app.main:app --reload --port 8000
} else {
    throw "No se encontró uv ni backend\.venv. Ejecuta .\scripts\setup.ps1 primero."
}
