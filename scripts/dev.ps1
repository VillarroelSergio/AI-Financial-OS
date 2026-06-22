$root = Split-Path $PSScriptRoot -Parent

Write-Host "Iniciando AI Financial OS..." -ForegroundColor Cyan

$backend = Start-Process -FilePath "uv" `
    -ArgumentList "run", "uvicorn", "app.main:app", "--reload", "--port", "8000" `
    -WorkingDirectory "$root\backend" `
    -PassThru `
    -NoNewWindow

Write-Host "  Backend iniciado en http://127.0.0.1:8000 (PID $($backend.Id))" -ForegroundColor Green

Start-Sleep -Seconds 2

$frontend = Start-Process -FilePath "npm" `
    -ArgumentList "run", "tauri", "dev" `
    -WorkingDirectory "$root\apps\desktop" `
    -PassThru `
    -NoNewWindow

Write-Host "  Desktop iniciando... (primera vez puede tardar varios minutos)" -ForegroundColor Green
Write-Host "Presiona Ctrl+C para detener." -ForegroundColor Yellow

try {
    Wait-Process -Id $backend.Id -ErrorAction SilentlyContinue
    Wait-Process -Id $frontend.Id -ErrorAction SilentlyContinue
} finally {
    if (-not $backend.HasExited) { $backend.Kill() }
    if (-not $frontend.HasExited) { $frontend.Kill() }
    Write-Host "Procesos detenidos." -ForegroundColor Gray
}
