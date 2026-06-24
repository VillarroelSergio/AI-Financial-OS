$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$backend = $null
$desktop = $null
$backendPort = 8010
$backendUrl = "http://127.0.0.1:$backendPort"

Write-Host "Iniciando AI Financial OS..." -ForegroundColor Cyan

try {
try {
    $health = Invoke-RestMethod "$backendUrl/health" -TimeoutSec 2
    if ($health.status -eq "ok") {
        Write-Host "  Backend ya iniciado en $backendUrl" -ForegroundColor Green
    }
} catch {
    $listener = Get-NetTCPConnection -LocalPort $backendPort -State Listen -ErrorAction SilentlyContinue
    if ($listener) {
        throw "El puerto $backendPort está ocupado por el proceso $($listener.OwningProcess)."
    }

    $uv = Get-Command "uv" -ErrorAction SilentlyContinue
    $venvPython = Join-Path $root "backend\.venv\Scripts\python.exe"
    if ($uv) {
        $backendCommand = $uv.Source
        $backendArguments = @("run", "uvicorn", "app.main:app", "--reload", "--port", "$backendPort")
    } elseif (Test-Path $venvPython) {
        $backendCommand = $venvPython
        $backendArguments = @("-m", "uvicorn", "app.main:app", "--reload", "--port", "$backendPort")
    } else {
        throw "No se encontró uv ni backend\.venv. Ejecuta .\scripts\setup.ps1."
    }

    $backend = Start-Process -FilePath $backendCommand -ArgumentList $backendArguments `
        -WorkingDirectory "$root\backend" -PassThru -NoNewWindow
    Start-Sleep -Seconds 2
    if ($backend.HasExited) { throw "El backend terminó durante el arranque." }
    Write-Host "  Backend iniciado en $backendUrl" -ForegroundColor Green
}

$npmCommand = if ($IsWindows -or $env:OS -eq "Windows_NT") { "npm.cmd" } else { "npm" }
$desktop = Start-Process -FilePath $npmCommand -ArgumentList @("run", "tauri", "dev") `
    -WorkingDirectory "$root\apps\desktop" -PassThru -NoNewWindow
Write-Host "  Desktop iniciando... la primera compilación puede tardar varios minutos" -ForegroundColor Green
Write-Host "Presiona Ctrl+C para detener ambos procesos." -ForegroundColor Yellow

Wait-Process -Id $desktop.Id
$desktop.Refresh()
if ($desktop.ExitCode -ne 0) {
    throw "Tauri terminó inesperadamente. Revisa el error mostrado justo arriba."
}
}
finally {
    if ($desktop -and -not $desktop.HasExited) { Stop-Process -Id $desktop.Id -Force }
    if ($backend -and -not $backend.HasExited) { Stop-Process -Id $backend.Id -Force }
    Write-Host "Procesos detenidos." -ForegroundColor Gray
}
