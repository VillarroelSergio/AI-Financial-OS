# Spec: Fase 3+4 — Investments (Portfolio Tracker)

**Fecha:** 2026-06-23  
**Estado:** Aprobado por usuario  
**Fusiona:** Fase 3 (Investments Basic) + Fase 4 (Market Watch para activos de inversión)

---

## Contexto y objetivo

El usuario tiene tres fuentes de inversión:
- **Trade Republic** — acciones individuales (mercados mixtos: ES, EU, US) + cuenta remunerada
- **Finizens** — roboadvisor, Plan USA con 3 fondos institucionales

El objetivo es una pantalla de inversiones que responda: **"¿Cómo evolucionan mis inversiones?"** con precios actualizados automáticamente via yfinance para activos con ticker, y con NAV manual puntual para los fondos institucionales de Finizens que no están en Yahoo Finance.

El usuario no introduce datos manualmente de forma recurrente. La composición de la cartera (tickers, ISINs, cantidades, precios de compra) se introduce **una sola vez** como configuración inicial.

---

## Alcance

### Incluye

- Modelos de datos: `InvestmentAsset`, `Holding`, `InvestmentOperation`
- Servicio de precios: `yfinance` para tickers, NAV manual para fondos sin ticker
- Caché de precios en SQLite con timestamp
- Refresh manual bajo demanda
- Pantalla Inversiones completa con Design System aplicado
- Diálogos de alta de acciones, fondos y cuenta remunerada
- `ManualNavDialog` para actualizar NAV de fondos Finizens
- Empty states, loading skeletons, estados de error
- UX snapshot registrado en `snapshot-routes.ts`
- Mock data en `mock-data.ts`

### No incluye

- Importación automática desde brokers o scraping
- Streaming de precios en tiempo real (solo refresh manual)
- Comparativa con índices (Fase 4 completa)
- Cripto
- Cuenta remunerada TR como tipo de activo especial con interés compuesto — se modela como `savings_account` con TAE simple

---

## Arquitectura

### Reutilización de `Account`

Se reutilizan las cuentas existentes (`Account.type = broker | investment | savings`). No se crea un modelo de cuenta de inversión separado.

- Trade Republic acciones → Account `broker`
- Finizens → Account `investment`  
- Cuenta remunerada TR → Account `savings`

### Nuevos modelos SQLAlchemy

**`InvestmentAsset`**
```
id              UUID PK
name            str — nombre legible (ej. "Apple Inc.")
ticker          str | null — símbolo yfinance (ej. "AAPL", "TEF.MC")
isin            str | null — ISIN del fondo/activo
asset_type      enum: stock | etf | fund | savings_account
currency        str — ISO 4217 (ej. "USD", "EUR")
region          str | null
sector          str | null
price_source    enum: yfinance | manual — determina cómo se actualiza el precio
created_at      datetime UTC
updated_at      datetime UTC
```

**`Holding`**
```
id                      UUID PK
account_id              FK → accounts.id
asset_id                FK → investment_assets.id
quantity                Decimal(18,8) — participaciones o acciones
average_price           Decimal(18,4) — precio medio de compra en divisa del activo
current_price           Decimal(18,4) | null — último precio conocido
current_price_currency  str
current_price_updated_at datetime UTC | null
market_value            Decimal(18,2) | null — quantity × current_price convertido a EUR (moneda base de la app)
interest_rate           Decimal(5,4) | null — solo para savings_account (TAE)
inception_date          date | null — fecha de inicio (para interés acumulado)
created_at              datetime UTC
updated_at              datetime UTC
```

**`InvestmentOperation`**
```
id              UUID PK
account_id      FK → accounts.id
asset_id        FK → investment_assets.id
date            date
operation_type  enum: buy | sell | deposit | withdrawal | dividend | interest | fee
quantity        Decimal(18,8) | null
price           Decimal(18,4) | null
amount          Decimal(18,2) — importe total en EUR
currency        str
fees            Decimal(18,2) default 0
source          str default "manual"
import_batch_id str | null
created_at      datetime UTC
updated_at      datetime UTC
```

---

## API Endpoints

Todos bajo `/api/investments/`:

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/assets` | Listar activos registrados |
| POST | `/assets` | Crear activo |
| PATCH | `/assets/{id}` | Actualizar activo |
| DELETE | `/assets/{id}` | Eliminar activo |
| GET | `/holdings` | Todos los holdings con P&L calculado |
| POST | `/holdings` | Añadir holding a una cuenta |
| PATCH | `/holdings/{id}` | Actualizar holding (cantidad, precio compra, NAV manual) |
| DELETE | `/holdings/{id}` | Eliminar holding |
| GET | `/operations` | Historial de operaciones |
| POST | `/operations` | Registrar operación |
| POST | `/prices/refresh` | Actualizar precios vía yfinance para todos los holdings con `price_source=yfinance` |
| GET | `/summary` | Totales: valor_total, aportado, rentabilidad_abs, rentabilidad_pct, by_account |

### Endpoint `GET /holdings` — respuesta enriquecida

Cada holding devuelve campos calculados (no persistidos):
- `cost_basis` = quantity × average_price (convertido a EUR)
- `return_absolute` = market_value - cost_basis
- `return_percent` = (return_absolute / cost_basis) × 100
- Para `savings_account`: `accrued_interest` calculado desde `inception_date` con `interest_rate`

### Endpoint `POST /prices/refresh`

1. Filtra holdings con `price_source = yfinance` y `ticker` no nulo
2. Llama `yfinance.Ticker(ticker).fast_info` en batch
3. Actualiza `current_price`, `current_price_updated_at`, `market_value` en DB
4. Responde con: `{ updated: N, failed: [...tickers que fallaron], needs_manual_nav: [...asset_ids sin ticker] }`

El frontend usa `needs_manual_nav` para abrir `ManualNavDialog` automáticamente.

---

## Servicio de precios (`PriceService`)

```python
# backend/app/modules/investments/price_service.py

class PriceService:
    def refresh_prices(db, holding_ids=None) -> PriceRefreshResult
    def fetch_ticker_price(ticker: str) -> Decimal | None  # yfinance
    def update_manual_nav(db, holding_id: str, nav: Decimal) -> Holding
```

- `yfinance` se instala como dependencia Python: `yfinance>=0.2`
- Los precios de acciones en USD se convierten a EUR usando el tipo de cambio EUR/USD también de yfinance (`ticker="EURUSD=X"`)
- Si yfinance falla para un ticker, se registra en `failed` y se mantiene el precio anterior

---

## Frontend

### Tipos nuevos (`src/lib/types/index.ts`)

```typescript
type AssetType = "stock" | "etf" | "fund" | "savings_account"
type PriceSource = "yfinance" | "manual"
type OperationType = "buy" | "sell" | "deposit" | "withdrawal" | "dividend" | "interest" | "fee"

interface InvestmentAsset { id, name, ticker, isin, asset_type, currency, region, sector, price_source, created_at, updated_at }
interface Holding { id, account_id, asset_id, quantity, average_price, current_price, current_price_currency, current_price_updated_at, market_value, interest_rate, inception_date, created_at, updated_at, asset: InvestmentAsset }
interface HoldingEnriched extends Holding { cost_basis, return_absolute, return_percent, accrued_interest? }
interface InvestmentOperation { id, account_id, asset_id, date, operation_type, quantity, price, amount, currency, fees, source, created_at }
interface InvestmentSummary { total_value, total_invested, return_absolute, return_percent, currency, by_account: AccountSummary[], last_updated }
interface PriceRefreshResult { updated, failed: string[], needs_manual_nav: string[] }
```

### API client (`src/lib/api/investments.ts`)

Funciones: `getHoldings`, `createHolding`, `updateHolding`, `deleteHolding`, `getAssets`, `createAsset`, `getOperations`, `createOperation`, `refreshPrices`, `getSummary`

### Hook (`src/lib/hooks/useInvestments.ts`)

```typescript
useInvestmentSummary() → { summary, loading, error, refresh }
useHoldings(accountId?) → { holdings, loading, error, refresh }
useOperations() → { operations, loading }
useRefreshPrices() → { refresh, refreshing, needsManualNav }
```

### Componentes nuevos

| Componente | Descripción |
|-----------|-------------|
| `HoldingRow` | Fila compacta: nombre + valor + badge P&L% |
| `InvestmentSummaryBar` | 3 MetricCards: Valor total / Aportado / Rentabilidad |
| `DistributionChart` | ChartCard con donut Recharts (por cuenta) |
| `PositionsTabs` | Card con tabs [Trade Republic] [Finizens] [Ahorro] |
| `SavingsAccountCard` | Saldo + TAE + interés acumulado |
| `AddStockDialog` | Modal: ticker + cantidad + precio compra + fecha |
| `AddFundDialog` | Modal: nombre + ISIN + participaciones + precio compra |
| `ManualNavDialog` | Modal mínimo: campo NAV actual por fondo |
| `AddSavingsDialog` | Modal: saldo + TAE + fecha inicio |

### Layout `InvestmentsPage`

```
p-xxxl space-y-xl

[Header row]
  "Inversiones" (text-heading-lg)
  "Última actualización: X" (caption stone)
  [↻ Actualizar precios] (button-secondary rounded-full)

[MetricCards: grid-cols-3 gap-xl]
  Valor total | Aportado | Rentabilidad (con borde top semántico)

[Main: grid-cols-5 gap-xl]
  [col-span-3] ChartCard "Distribución de cartera"
    Donut Recharts — 3 segmentos con colores del sistema
    Leyenda: nombre cuenta + valor + %

  [col-span-2] card "Posiciones"
    Tabs pill: [Trade Republic] [Finizens] [Ahorro]
    Por tab: lista compacta HoldingRow + botón ghost al pie

[Empty state]  ← si no hay holdings: EmptyState BarChart2 + botón añadir
```

---

## Design System aplicado

- Canvas: `canvas-dark #000000`, cards: `surface-elevated #16181a`, borde: `hairline-dark`
- Rentabilidad positiva: `accent-teal #00a87e`, negativa: `accent-danger #e23b4a`
- Donut colors: `#494fdf` (TR) / `#00a87e` (Finizens) / `#376cd5` (Ahorro)
- Botón refresh: `button-secondary rounded-full`
- Tabs broker: `button-pill-sm` (inactivo: surface-elevated + stone; activo: primary + on-primary)
- Modales: `rounded-xl`, `surface-elevated`, `text-input` estándar
- Todos los componentes implementan 5 estados: loading (skeleton) / empty / error / partial / success

---

## Flujo de actualización de precios

1. Usuario pulsa **↻ Actualizar precios**
2. Frontend llama `POST /api/investments/prices/refresh`
3. Backend actualiza vía yfinance todos los holdings con ticker
4. Si `needs_manual_nav` no está vacío → frontend abre `ManualNavDialog` para cada fondo
5. Usuario introduce NAV → `PATCH /api/investments/holdings/{id}` con `current_price`
6. UI refresca automáticamente con nuevos valores y P&L

---

## UX Snapshots

Añadir a `tools/ux-snapshot/snapshot-routes.ts`:
```typescript
{ path: "/investments", filename: "investments.png", screenName: "Investments", state: "mock_data", description: "Portfolio tracker con TR + Finizens + cuenta remunerada" }
{ path: "/investments", filename: "investments-empty.png", screenName: "Investments Empty", state: "empty", description: "Estado vacío sin posiciones registradas" }
```

Añadir fixtures de mock data en `apps/desktop/src/lib/api/mock-data.ts`:
- 2-3 acciones TR con precios y P&L
- 3 fondos Finizens con participaciones y NAV
- 1 cuenta remunerada con saldo y TAE

---

## Deuda técnica generada

| # | Deuda | Impacto |
|---|-------|---------|
| TD-04 | Conversión de divisas hardcoded (solo USD→EUR via yfinance EURUSD=X) | Medio — suficiente para V1 |
| TD-05 | Sin histórico de precios — solo precio actual cacheado | Bajo — la gráfica histórica va en Fase 4 completa |
| TD-06 | NAV de fondos Finizens siempre manual — sin proveedor automático | Bajo — los fondos institucionales no están en APIs gratuitas |

---

## Actualización del roadmap

Al completar esta fase, marcar en `docs/02_ROADMAP.md`:
- Fase 3 → ✅ Completa

Fase 4 (Market Watch) sigue pendiente en su totalidad — cubre datos de mercado generales (IBEX, índices globales, bonos, divisas) como pantalla independiente, no la actualización de precios de cartera personal implementada aquí.
