# Build de actualizacion Windows: versiona, compila release completo y publica un .exe NSIS.
# Uso:
#   .\scripts\build-update.ps1 -Version 0.1.1
#   .\scripts\build-update.ps1 -Version 0.1.1 -Notes "Fix backend startup without console"
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^\d+\.\d+\.\d+([-.+][0-9A-Za-z.-]+)?$')]
    [string]$Version,

    [string]$Notes = "Actualizacion manual de AI Financial OS.",

    [switch]$SkipBackend
)

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$desktopDir = Join-Path $root "apps\desktop"
$tauriConfPath = Join-Path $desktopDir "src-tauri\tauri.conf.json"
$cargoTomlPath = Join-Path $desktopDir "src-tauri\Cargo.toml"
$desktopPackagePath = Join-Path $desktopDir "package.json"
$desktopPackageLockPath = Join-Path $desktopDir "package-lock.json"
$backendPyprojectPath = Join-Path $root "backend\pyproject.toml"
$releaseDir = Join-Path $root "release"

function Write-Utf8NoBom {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Value
    )

    $encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Value, $encoding)
}

function Update-JsonVersion {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$NewVersion,
        [switch]$PackageLock
    )

    if (-not (Test-Path $Path)) { throw "No existe $Path" }
    $content = Get-Content $Path -Raw
    $limit = 1
    if ($PackageLock) {
        $limit = 2
    }

    $matches = [regex]::Matches($content, '("version"\s*:\s*)".*?"')
    if ($matches.Count -lt $limit) {
        throw "No se encontraron suficientes campos version en $Path"
    }

    $builder = New-Object System.Text.StringBuilder
    $lastIndex = 0
    for ($i = 0; $i -lt $limit; $i++) {
        $match = $matches[$i]
        [void]$builder.Append($content.Substring($lastIndex, $match.Index - $lastIndex))
        [void]$builder.Append($match.Groups[1].Value)
        [void]$builder.Append("`"$NewVersion`"")
        $lastIndex = $match.Index + $match.Length
    }
    [void]$builder.Append($content.Substring($lastIndex))
    $updated = $builder.ToString()

    Write-Utf8NoBom -Path $Path -Value $updated
}

function Update-TomlVersion {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$NewVersion
    )

    if (-not (Test-Path $Path)) { throw "No existe $Path" }
    $content = Get-Content $Path -Raw
    $updated = [regex]::Replace(
        $content,
        '(?m)^(version\s*=\s*)".*?"',
        ('$1"' + $NewVersion + '"'),
        1
    )
    Write-Utf8NoBom -Path $Path -Value $updated
}

Write-Host "[1/4] Actualizando version a $Version..." -ForegroundColor Cyan
Update-JsonVersion -Path $tauriConfPath -NewVersion $Version
Update-JsonVersion -Path $desktopPackagePath -NewVersion $Version
if (Test-Path $desktopPackageLockPath) {
    Update-JsonVersion -Path $desktopPackageLockPath -NewVersion $Version -PackageLock
}
Update-TomlVersion -Path $cargoTomlPath -NewVersion $Version
Update-TomlVersion -Path $backendPyprojectPath -NewVersion $Version

Write-Host "[2/4] Compilando release completo..." -ForegroundColor Cyan
Push-Location $root
try {
    if ($SkipBackend) {
        & (Join-Path $root "scripts\build-release.ps1") -SkipBackend
    } else {
        & (Join-Path $root "scripts\build-release.ps1")
    }
    if ($LASTEXITCODE -ne 0) { throw "build-release.ps1 fallo." }
} finally {
    Pop-Location
}

Write-Host "[3/4] Publicando instalador de actualizacion..." -ForegroundColor Cyan
$nsisDir = Join-Path $desktopDir "src-tauri\target\release\bundle\nsis"
if (-not (Test-Path $nsisDir)) { throw "No existe $nsisDir" }
$installer = Get-ChildItem $nsisDir -File -Include "*.exe" -Recurse |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
if (-not $installer) { throw "No se encontro ningun instalador .exe en $nsisDir" }

New-Item -ItemType Directory -Force $releaseDir | Out-Null
$updateExe = Join-Path $releaseDir "AI-Financial-OS-$Version-update.exe"
Copy-Item -Path $installer.FullName -Destination $updateExe -Force

Write-Host "[4/4] Generando changelog..." -ForegroundColor Cyan
$changelogPath = Join-Path $releaseDir "CHANGELOG-$Version.txt"
$commit = "desconocido"
try {
    $commit = git -C $root rev-parse --short HEAD
} catch {}

$changelog = @"
AI Financial OS $Version
Fecha: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Commit: $commit

Notas:
$Notes

Instalacion:
- Ejecutar AI-Financial-OS-$Version-update.exe encima de la instalacion actual.
- Los datos de usuario se conservan en %APPDATA%\FinancialAgent\.
"@

Write-Utf8NoBom -Path $changelogPath -Value $changelog

Write-Host "Update generado:" -ForegroundColor Green
Write-Host "  $updateExe" -ForegroundColor Green
Write-Host "  $changelogPath" -ForegroundColor Green
