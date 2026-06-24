# Spec: Fase 5 — Economic Intelligence
**Fecha:** 2026-06-24
**Estado:** Aprobado

---

## Objetivo

Incorporar datos macroeconómicos reales (España, Eurozona, EEUU) con caché local, snapshot visual y comparativas deterministas de impacto personal, sin IA.

---

## Arquitectura backend

```
modules/economic_data/
  providers/
    __init__.py
    fred_provider.py          # FRED API — todos los indicadores macro
    stooq_macro_provider.py   # Reutiliza lógica market_data para euríbor, bonos, índices
  __init__.py
  schemas.py                  # IndicatorOut, RegionSnapshotOut, MacroSnapshotOut, PersonalImpactOut
  repository.py               # DuckDB cache — economic_indicators_cache
  service.py                  # Orquestación providers + cache + cálculo impact
  routes.py                   # Endpoints REST
```

### FredProvider

- Fuente: `https://api.stlouisfed.org/fred/series/observations`
- API key: `FRED_API_KEY` (variable de entorno)
- Series configuradas para cada indicador × región:

| Indicador          | España        | Eurozona       | EEUU          |
|--------------------|---------------|----------------|---------------|
| Inflación          | `ESPCPIALLMINMEI` | `CP0000EZ19M086NEST` | `CPIAUCSL` |
| Inflación subyacente | `ESPCORECPIALLMINMEI` | `CPGRLE01EZM659N` | `CPILFESL` |
| Paro               | `LRHUTTTTESM156S` | `LRHUTTTTEZM156S` | `UNRATE` |
| PIB (trimestral)   | `CLVMNACSCAB1GQES` | `CLVMNACSCAB1GQEA19` | `GDPC1` |
| Tipo política      | n/a (BCE)     | `ECBDFR` (BCE deposit rate) | `FEDFUNDS` |

- Frecuencia de refresco: datos mensuales/trimestrales → TTL 24h; datos diarios → TTL 4h.

### StooqMacroProvider

Wrapper ligero sobre los providers existentes (ya funcionando en Fase 4.6):
- **Euríbor 3M**: símbolo `EUR3M` en Stooq
- **Bono España 10Y, Bund 10Y, Treasury 10Y**: ya en `market_data_config.yaml`
- **IBEX 35, Euro Stoxx 50, S&P 500, Nasdaq, Dow Jones**: ídem
- **EUR/USD**: ídem

No duplicar lógica — llamar directamente al `ProviderRouter` de market_data para estos activos y adaptar la respuesta al modelo `IndicatorOut`.

---

## Modelo de caché (DuckDB)

Tabla `economic_indicators_cache`:

```sql
CREATE TABLE IF NOT EXISTS economic_indicators_cache (
    series_id     VARCHAR NOT NULL,
    region        VARCHAR NOT NULL,   -- ES, EA, US, GLOBAL
    indicator     VARCHAR NOT NULL,   -- inflation, core_inflation, unemployment, gdp, policy_rate, bond_10y, euribor, index, forex
    value         DOUBLE,
    prev_value    DOUBLE,             -- dato anterior para calcular variación
    period        VARCHAR,            -- "2026-05" / "2026-Q1"
    unit          VARCHAR,            -- "%", "pp", "index", "bps"
    source        VARCHAR,            -- "FRED", "STOOQ"
    observation_date DATE,
    downloaded_at TIMESTAMP DEFAULT current_timestamp,
    PRIMARY KEY (series_id, observation_date)
);
```

---

## Schemas (Pydantic)

```python
class IndicatorOut(BaseModel):
    series_id: str
    region: str                # "ES" | "EA" | "US"
    indicator: str
    name: str                  # nombre legible
    value: float | None
    prev_value: float | None
    change: float | None       # value - prev_value
    period: str                # "mayo 2026"
    unit: str
    source: str
    observation_date: str
    is_stale: bool

class RegionSnapshotOut(BaseModel):
    region: str
    indicators: list[IndicatorOut]

class MacroSnapshotOut(BaseModel):
    spain: RegionSnapshotOut
    eurozone: RegionSnapshotOut
    us: RegionSnapshotOut
    last_refreshed: str

class PersonalImpactOut(BaseModel):
    inflation_vs_savings: ImpactItem    # inflación ES vs tasa de ahorro usuario
    rates_vs_liquidity: ImpactItem      # tipo BCE vs rentabilidad media cuentas remuneradas
    market_vs_portfolio: ImpactItem     # variación índices vs rentabilidad cartera
    purchasing_power: ImpactItem        # inflación 12m acumulada vs variación ingresos

class ImpactItem(BaseModel):
    title: str
    macro_value: float | None
    personal_value: float | None
    delta: float | None
    interpretation: str     # "favorable" | "neutral" | "adverse"
    description: str        # texto fijo, sin IA
```

---

## Endpoints

```
GET  /api/economy/snapshot          → MacroSnapshotOut
GET  /api/economy/indicators        → list[IndicatorOut]  (query: region?, indicator?)
POST /api/economy/refresh           → MacroSnapshotOut    (fuerza descarga fresca)
GET  /api/economy/impact            → PersonalImpactOut
```

---

## PersonalImpact — lógica determinista

### 1. Inflación vs tasa de ahorro
- `macro_value`: inflación España último dato (%)
- `personal_value`: `(ingresos - gastos) / ingresos * 100` del último mes completo con datos
- `delta`: personal_value - macro_value
- `interpretation`: favorable si delta > 0 (ahorro supera inflación), adverse si delta < 0

### 2. Tipo BCE vs liquidez
- `macro_value`: tipo depósito BCE (%)
- `personal_value`: rentabilidad media ponderada de cuentas remuneradas del usuario (saldo × tasa configurada en la cuenta). Si el usuario no tiene cuentas remuneradas → `None`
- `interpretation`: favorable si personal_value >= macro_value

### 3. Mercado vs cartera
- `macro_value`: variación 12m del Euro Stoxx 50 (%)
- `personal_value`: rentabilidad 12m de la cartera de inversiones del usuario (%)
- `interpretation`: favorable si personal_value >= macro_value

### 4. Poder adquisitivo
- `macro_value`: inflación acumulada 12 meses España
- `personal_value`: variación de ingresos medios (último trimestre vs año anterior) del usuario
- `interpretation`: favorable si ingresos crecen más que inflación

Si el usuario no tiene datos suficientes para calcular `personal_value`, se devuelve `None` y `interpretation: "sin_datos"`.

---

## UI — EconomyPage

```
EconomyPage
 ├─ Header: "Economía" + botón Refresh (spinner durante fetch)
 ├─ LastUpdated chip
 ├─ GlobalSnapshot: 4 IndicatorCard destacadas
 │    (Inflación ES | Tipo BCE | Fed Funds | EUR/USD)
 ├─ Tabs: España | Eurozona | EEUU
 │    cada tab: grid de IndicatorCard
 └─ PersonalImpact: 4 ImpactCard con semáforo (verde/gris/rojo)
```

### IndicatorCard
```
Inflación España
3,2 %
▲ +0,4 pp vs mayo 2026
Fuente: INE (vía FRED) · mayo 2026
```

### ImpactCard
```
Inflación vs tu ahorro
Inflación: 3,2%   Tu tasa de ahorro: 18,4%
✅ Ahorras por encima de la inflación
```

---

## Configuración

- `FRED_API_KEY` en `.env` y en `.env.example` (vacío)
- Sin key → FredProvider devuelve `is_stale: true` con `value: None`; la UI muestra "Configura FRED_API_KEY para ver este dato"

---

## Tests (~20)

- `FredProvider`: mock HTTP, parsing correcto, error handling sin key
- `StooqMacroProvider`: adapta `QuoteOut` → `IndicatorOut`
- `repository`: insert + cache hit, TTL expirado
- `service`: orquestación, fallback a caché si provider falla
- `routes`: GET snapshot (200), POST refresh (200/409 si en curso)
- `PersonalImpact`: cada uno de los 4 cálculos (favorable, adverse, sin_datos)
