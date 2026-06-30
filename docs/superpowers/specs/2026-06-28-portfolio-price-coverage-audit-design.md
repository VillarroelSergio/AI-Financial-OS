# Portfolio Price Coverage Audit — Design Spec

**Date:** 2026-06-28  
**Status:** Approved  
**Phase:** Pre-Portfolio Import Assistant

---

## Objetivo

Validar si AI Financial OS puede consultar y actualizar automáticamente los precios actuales de las acciones individuales de la cartera del usuario, antes de implementar el importador por captura.

Responde de forma fiable:
- ¿Podemos actualizar automáticamente esta acción?
- ¿Qué ticker correcto debemos usar?
- ¿Qué proveedor devuelve precio válido?
- ¿En qué divisa viene el precio?
- ¿Cuándo se actualizó por última vez?
- ¿Qué activos deben quedar como actualización manual?

---

## Contexto del proyecto

Stack: Tauri + React + TypeScript + Tailwind + shadcn/ui + Python + FastAPI + SQLite + DuckDB + Ollama/LM Studio.

Módulos relevantes:
- `backend/app/modules/investments/` — CRUD de holdings, `PriceService` (usa yfinance directo)
- `backend/app/modules/market_intelligence/` — `ProviderOrchestrator`, adapters (Finnhub, Alpha Vantage, Polygon, Twelve Data, CoinGecko), modelos `MarketQuote`/`AdapterResult`

Gap actual: los holdings usan yfinance directamente. Market Intelligence existe pero no se usa para price refresh de holdings individuales. Esta feature construye el puente.

---

## Activos de referencia (19 activos)

| Nombre | Ticker | Exchange | Divisa |
|--------|--------|----------|--------|
| Banco Bilbao Vizcaya Argentaria SA | BBVA | BME | EUR |
| Apple | AAPL | NASDAQ | USD |
| Iberdrola | IBE.MC | BME | EUR |
| ASML | ASML | AMS | EUR |
| Caterpillar | CAT | NYSE | USD |
| Alphabet (A) | GOOGL | NASDAQ | USD |
| Waste Management | WM | NYSE | USD |
| TSMC (ADR) | TSM | NYSE | USD |
| Johnson & Johnson | JNJ | NYSE | USD |
| Lockheed Martin | LMT | NYSE | USD |
| NVIDIA | NVDA | NASDAQ | USD |
| SpaceX | SPCX | NASDAQ | USD |
| Amazon.com | AMZN | NASDAQ | USD |
| Rocket Lab | RKLB | NASDAQ | USD |
| RTX Corporation | RTX | NYSE | USD |
| Berkshire Hathaway (B) | BRK-B | NYSE | USD |
| Visa | V | NYSE | USD |
| Microsoft | MSFT | NASDAQ | USD |
| DroneShield | DRO.AX | ASX | AUD |

Notas:
- `BBVA` en yfinance se resuelve como `BBVA.MC`
- `ASML` en yfinance se resuelve como `ASML.AS`
- `BRK-B` en yfinance puede requerir `BRK.B`

---

## Arquitectura

```
AssetResolutionService
  ├── known_tickers dict (19 activos hardcodeados para resolución)
  ├── yfinance probe para activos fuera de la lista
  └── Output: AssetResolution (candidates, selected, status)

EquityQuoteService (wrapper ligero sobre adapters MI)
  ├── Itera adapters MI por prioridad: Finnhub → AlphaVantage → TwelveData → Polygon
  ├── Fallback final: yfinance
  ├── Registra: provider usado, timestamp, freshness
  └── Output: EquityQuoteResult (price, currency, provider, retrieved_at, from_cache)

PriceCoverageAuditService
  ├── Recibe lista de asset_names
  ├── → AssetResolutionService → ticker + exchange + currency esperada
  ├── → EquityQuoteService → precio real + provider + freshness
  ├── → Clasificación de estado (OK/PARTIAL/AMBIGUOUS/UNAVAILABLE/MANUAL/ERROR)
  ├── → Validación de divisa (requires_fx_conversion)
  └── Output: AuditReport
```

### Decisión de integración con Market Intelligence

**Opción elegida: B — Wrapper ligero sobre adapters MI.**

- Llama directamente a los adapters existentes (Finnhub, Alpha Vantage, etc.) para un ticker dado, sin pasar por el orchestrator/catalog YAML
- No requiere crear catálogo YAML de equities
- Registra qué provider respondió (visible en reporte)
- Deja preparado el puente con MI para fases futuras
- No crea sistema paralelo

---

## Estados de cobertura

| Estado | Condición |
|--------|-----------|
| `OK` | Ticker resuelto + precio válido + divisa coherente + dato < 24h |
| `PARTIAL` | Precio disponible pero: dato 24h–72h, divisa requiere FX, o provider secundario |
| `AMBIGUOUS` | Varios tickers posibles, requiere confirmación del usuario |
| `UNAVAILABLE` | Ningún provider devuelve precio (dato > 72h o ausente) |
| `MANUAL` | Activo no cotizado públicamente |
| `ERROR` | Fallo técnico controlado — sin stacktrace expuesto al usuario |

### Lógica de freshness

- < 24h → fresco → OK
- 24h – 72h → retrasado → PARTIAL + warning
- > 72h o ausente → UNAVAILABLE

### Divisas y FX

Divisa esperada por ticker hardcodeada en el dict de resolución. Si el precio llega en divisa diferente → warning. Si cartera en EUR y precio en USD/AUD → `requires_fx_conversion: true` → estado `PARTIAL`. No se convierte (no hay sistema FX implementado), se documenta.

### Fallback chain

```
1. Provider principal (Finnhub u otro de mayor prioridad con API key)
2. Provider secundario (siguiente en prioridad)
3. yfinance (sin API key, siempre disponible)
4. Último precio cacheado si existe
5. UNAVAILABLE
```

Si el activo es MANUAL → no consulta ningún provider.

---

## Módulos y archivos nuevos

### Backend

```
backend/app/modules/investments/
  asset_resolution.py          ← AssetResolutionService
  price_coverage_audit.py      ← PriceCoverageAuditService

backend/app/modules/market_intelligence/ingestion/
  equity_quote_service.py      ← EquityQuoteService (wrapper adapters MI)
```

### API endpoints

```
GET  /api/investments/price-coverage/default-assets
POST /api/investments/price-coverage/audit
POST /api/investments/price-coverage/resolve
```

Registrados en `backend/app/modules/investments/routes.py` (o archivo de rutas separado `price_coverage_routes.py`).

No se persiste el reporte en base de datos — generado on-demand. Estructura opcional para futura persistencia:
```sql
price_coverage_audit(id, generated_at, payload_json)
```

### Schemas de respuesta

**POST /audit response:**
```json
{
  "generated_at": "2026-06-28T00:00:00Z",
  "summary": {
    "total": 19, "ok": 0, "partial": 0,
    "ambiguous": 0, "manual": 0, "unavailable": 0, "error": 0
  },
  "assets": [
    {
      "asset_name": "Apple",
      "selected_ticker": "AAPL",
      "exchange": "NASDAQ",
      "currency": "USD",
      "provider": "finnhub",
      "price": 0.00,
      "price_currency": "USD",
      "requires_fx_conversion": false,
      "last_update": "2026-06-28T00:00:00Z",
      "freshness_hours": 0.5,
      "from_cache": false,
      "status": "OK",
      "confidence": 0.95,
      "notes": []
    }
  ]
}
```

**POST /resolve response:**
```json
{
  "asset_name": "BBVA",
  "candidates": [
    {
      "ticker": "BBVA",
      "yfinance_symbol": "BBVA.MC",
      "name": "Banco Bilbao Vizcaya Argentaria SA",
      "exchange": "BME",
      "currency": "EUR",
      "asset_type": "equity",
      "confidence": 0.98
    }
  ],
  "selected": { "ticker": "BBVA", "exchange": "BME", "currency": "EUR" },
  "status": "resolved"
}
```

---

## Frontend

### Ubicación

```
Inversiones → Herramientas → Cobertura de precios
```

### Componentes nuevos

```
apps/desktop/src/features/investments/price-coverage/
  PriceCoveragePage.tsx
  PriceCoverageTable.tsx
  PriceCoverageStatusBadge.tsx
  AssetResolutionDialog.tsx
  PriceCoverageSummaryCards.tsx
```

### UX (Dark Premium)

```
Header: Cobertura de precios
Subtítulo: Comprueba si tus acciones pueden actualizarse automáticamente.

Tarjetas resumen:
  OK | Revisar | Manual | Sin cobertura

Tabla:
  Activo | Ticker | Mercado | Divisa | Proveedor | Precio | Estado | Última act. | Acciones

Acciones por fila:
  Reintentar | Resolver ticker (si AMBIGUOUS)
```

Mensajes de estado claros al usuario (sin términos técnicos).

---

## Tests backend

Archivo: `backend/app/tests/test_price_coverage.py`

Casos cubiertos:
- Apple → AAPL resuelto, exchange NASDAQ, currency USD
- Iberdrola → IBE.MC resuelto, exchange BME, currency EUR
- BBVA → BBVA resuelto (yfinance: BBVA.MC), exchange BME, currency EUR
- ASML → ASML resuelto (yfinance: ASML.AS), exchange AMS, currency EUR
- SpaceX → SPCX resuelto, exchange NASDAQ, currency USD
- DroneShield → DRO.AX resuelto, exchange ASX, currency AUD
- Audit clasifica OK cuando provider devuelve precio fresco
- Audit clasifica UNAVAILABLE cuando todos los providers fallan
- Audit clasifica PARTIAL cuando dato tiene > 24h o requiere FX
- Audit no rompe si un provider lanza excepción
- Endpoint POST /audit devuelve summary con totales correctos

Todos los providers mockeados — sin dependencia de internet.

---

## Documentación

Crear:
- `docs/18_PORTFOLIO_PRICE_COVERAGE_AUDIT.md`

Actualizar:
- `docs/02_ROADMAP.md`
- `docs/04_DATA_MODEL.md`
- `docs/11_API_CONTRACT.md`
- `docs/13_CLAUDE_CODE_GUIDE.md`

---

## Restricciones

- No hardcodear precios — solo tickers/exchanges/divisas esperadas
- No inventar tickers
- No introducir scraping del broker
- No introducir automatización bancaria
- No enviar datos a cloud
- No romper Fase 6 ni Market Intelligence existente
- Datos locales únicamente

---

## Criterios de aceptación

1. Servicio de resolución de activos implementado
2. Servicio de auditoría de cobertura implementado
3. Lista inicial de 19 activos auditables
4. SpaceX resuelve a SPCX (NASDAQ)
5. BBVA resuelve a BBVA (BME, yfinance: BBVA.MC)
6. ASML resuelve a ASML (AMS, yfinance: ASML.AS)
7. DroneShield resuelve a DRO.AX (ASX)
8. Sistema reutiliza adapters de Market Intelligence
9. No hay precios hardcodeados
10. Endpoint POST /api/investments/price-coverage/audit funcional
11. UI de Cobertura de precios en Inversiones
12. UI muestra resumen y tabla con estados
13. Estados OK/PARTIAL/AMBIGUOUS/UNAVAILABLE/MANUAL/ERROR implementados
14. Tests backend principales pasan con providers mockeados
15. No se rompe Market Intelligence ni módulo de inversiones existente
16. Documentación actualizada

---

## Próximo paso

Implementar **Portfolio Import Assistant** — importador por captura que reutilizará:
- Resolución de tickers (asset_resolution.py)
- Estado automatic/manual por activo
- price_update_mode
- Warnings por activo
- Candidatos de ticker
- Soporte para activos no cotizados
