# Smoke test post-build (Fase 11): lanza el binario de release, espera /health,
# comprueba que la app sigue viva y cierra limpio.
# Uso: .\scripts\smoke-test.ps1 [-ExePath <ruta>] [-TimeoutSec 60]
param(
    [string]$ExePath,
    [int]$TimeoutSec = 60
)
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
if (-not $ExePath) {
    $ExePath = Join-Path $root "apps\desktop\src-tauri\target\release\AI Financial OS.exe"
}
if (-not (Test-Path $ExePath)) { throw "No existe $ExePath. Ejecuta .\scripts\build-release.ps1 primero." }

$healthUrl = "http://127.0.0.1:8010/health"

# Precondición: el puerto debe estar libre para probar el arranque real del bundle.
$portBusy = $false
try { Invoke-RestMethod $healthUrl -TimeoutSec 2 | Out-Null; $portBusy = $true } catch {}
if ($portBusy) { throw "Ya hay un backend sirviendo $healthUrl — ciérralo para un smoke test limpio." }

Write-Host "Lanzando $ExePath..." -ForegroundColor Cyan
$app = Start-Process -FilePath $ExePath -PassThru
$deadline = (Get-Date).AddSeconds($TimeoutSec)
$healthy = $false
$sw = [System.Diagnostics.Stopwatch]::StartNew()

while ((Get-Date) -lt $deadline) {
    if ($app.HasExited) { throw "La aplicación terminó durante el arranque (exit code $($app.ExitCode))." }
    try {
        $health = Invoke-RestMethod $healthUrl -TimeoutSec 2
        if ($health.status -eq "ok") { $healthy = $true; break }
    } catch {}
    Start-Sleep -Milliseconds 500
}

if (-not $healthy) {
    Stop-Process -Id $app.Id -Force -ErrorAction SilentlyContinue
    throw "SMOKE TEST FALLIDO: /health no respondió 200 en $TimeoutSec s."
}
Write-Host "  /health OK en $([math]::Round($sw.Elapsed.TotalSeconds, 1)) s" -ForegroundColor Green

Start-Sleep -Seconds 3
$app.Refresh()
if ($app.HasExited) { throw "SMOKE TEST FALLIDO: la app se cerró tras el arranque." }
Write-Host "  Ventana estable tras arranque" -ForegroundColor Green

# Cierre educado (WM_CLOSE) para que Tauri dispare RunEvent::Exit y mate al backend.
$app.CloseMainWindow() | Out-Null
if (-not $app.WaitForExit(10000)) {
    Stop-Process -Id $app.Id -Force
    throw "SMOKE TEST FALLIDO: la app no cerró tras CloseMainWindow."
}
Start-Sleep -Seconds 3

# El proceso hijo del backend debe morir con la app.
$orphan = $null
try { $orphan = Invoke-RestMethod $healthUrl -TimeoutSec 2 } catch {}
if ($orphan) {
    Get-Process financial-backend -ErrorAction SilentlyContinue | Stop-Process -Force
    throw "SMOKE TEST FALLIDO: el backend quedó huérfano tras cerrar la app."
}
Write-Host "  Backend cerrado con la app" -ForegroundColor Green
Write-Host "SMOKE TEST OK" -ForegroundColor Green
