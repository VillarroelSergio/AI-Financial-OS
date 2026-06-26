# Fase 2 — CSV Import Center

## Entrega

Importación local y reversible para Monefy CSV y CSV genérico: fuente, archivo, preview, validación, confirmación, resumen, historial y rollback.

## Decisiones

- `ImportBatch` e `ImportRow` aportan trazabilidad sin escribir filas financieras en logs.
- UTF-8 con BOM, fechas `D/M/YYYY`, importes con punto o coma y monedas ISO.
- La huella de duplicado combina fecha, importe, descripción normalizada y categoría.
- La confirmación crea cuentas y categorías inexistentes y vincula cada movimiento al lote.
- `?demo=preview` genera snapshots reproducibles con datos ficticios.

## Verificación

```powershell
cd backend
uv run pytest
uv run ruff check app
cd ..\apps\desktop
npm run build
npm run ux:snapshots
```
