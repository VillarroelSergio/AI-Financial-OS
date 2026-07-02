# Build de release Windows (Fase 11): backend PyInstaller + tauri build (.msi / .exe NSIS).
# Uso: .\scripts\build-release.ps1 [-SkipBackend]
param(
    [switch]$SkipBackend
)
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$backendDir = Join-Path $root "backend"
$desktopDir = Join-Path $root "apps\desktop"
$binariesDir = Join-Path $desktopDir "src-tauri\binaries\backend"
$env:UV_CACHE_DIR = Join-Path $root ".uv-cache"

# 1. Backend -> dist\financial-backend (onedir)
if (-not $SkipBackend) {
    Write-Host "[1/3] Compilando backend con PyInstaller..." -ForegroundColor Cyan
    Set-Location $backendDir
    uv sync --group build
    if ($LASTEXITCODE -ne 0) { throw "uv sync falló." }
    uv run --group build pyinstaller financial-backend.spec --noconfirm --clean
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller falló." }
} else {
    Write-Host "[1/3] Backend omitido (-SkipBackend)." -ForegroundColor Yellow
}

# 2. Copiar backend a resources de Tauri
Write-Host "[2/3] Copiando backend a src-tauri\binaries\backend..." -ForegroundColor Cyan
$backendDist = Join-Path $backendDir "dist\financial-backend"
if (-not (Test-Path (Join-Path $backendDist "financial-backend.exe"))) {
    throw "No existe $backendDist\financial-backend.exe. Ejecuta sin -SkipBackend."
}
if (Test-Path $binariesDir) { Remove-Item $binariesDir -Recurse -Force }
New-Item -ItemType Directory -Force $binariesDir | Out-Null
Copy-Item "$backendDist\*" $binariesDir -Recurse

# 3. Frontend + bundle Tauri
Write-Host "[3/3] Ejecutando tauri build..." -ForegroundColor Cyan
Set-Location $desktopDir
npm run tauri build
if ($LASTEXITCODE -ne 0) { throw "tauri build falló." }

$bundleDir = Join-Path $desktopDir "src-tauri\target\release\bundle"
Write-Host "Build completado. Instaladores en:" -ForegroundColor Green
Get-ChildItem $bundleDir -Recurse -Include *.msi, *setup.exe | ForEach-Object {
    Write-Host "  $($_.FullName)" -ForegroundColor Green
}
