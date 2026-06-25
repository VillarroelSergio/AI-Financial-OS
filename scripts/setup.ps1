$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent

Write-Host "AI Financial OS — Setup" -ForegroundColor Cyan

# Directorio data
if (-not (Test-Path "$root\data")) {
    New-Item -ItemType Directory -Path "$root\data" | Out-Null
    Write-Host "  Creado: data/" -ForegroundColor Gray
}

# .env
if (-not (Test-Path "$root\.env")) {
    Copy-Item "$root\.env.example" "$root\.env"
    Write-Host "  Creado: .env desde .env.example" -ForegroundColor Gray
}

# Python
Write-Host "Instalando dependencias Python..." -ForegroundColor Yellow
Set-Location "$root\backend"
$uv = Get-Command "uv" -ErrorAction SilentlyContinue
if ($uv) {
    & $uv.Source sync
} elseif (Test-Path ".venv\Scripts\python.exe") {
    & ".venv\Scripts\python.exe" -m pip install -e ".[dev]"
} else {
    throw "No se encontró uv. Instálalo desde https://docs.astral.sh/uv/ o crea backend\.venv."
}
Write-Host "  Backend OK" -ForegroundColor Green

# Node
Write-Host "Instalando dependencias Node..." -ForegroundColor Yellow
Set-Location "$root\apps\desktop"
npm install
Write-Host "  Desktop OK" -ForegroundColor Green

Write-Host "Setup completado. Ejecuta .\scripts\dev.ps1 para iniciar." -ForegroundColor Cyan
