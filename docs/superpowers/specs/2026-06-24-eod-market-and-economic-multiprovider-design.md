# Spec: EOD Market Data Simplification + Economic Intelligence Multi-Provider

**Fecha:** 2026-06-24  
**Fases afectadas:** 4.x (market data) y 5.x (economic intelligence)  
**Estado:** Aprobado

---

## Contexto y motivación

El sistema de market data actual (Fases 4.5 y 4.6) implementa fetch paralelo, ConsensusEngine y TTLs de 15–900s orientados a datos cuasi-en-tiempo-real. En la práctica los providers gratuitos devuelven datos EOD o con delay de 15 min, y la complejidad de refresh manual y estados "live/fresh/delayed" confunde al usuario sin aportar valor real.

El módulo de economic intelligence (Fase 5) solo usa FRED como fuente de datos macro. Esto crea dependencia de una única API key y deja fuera providers europeos más autoritativos (ECB para Eurozona) y validadores globales (OECD, World Bank).

Este spec cubre dos cambios independientes pero coordinados.

---

## Parte 1 — Market Data EOD Simplification

### Objetivo

Reducir el contrato de datos de mercado a **cierre del día anterior, una única llamada al arranque**. Sin refresh manual. Sin estados "live". Sin complejidad de presupuesto de requests para datos de mercado.

### Contrato de datos

- `freshness_status` solo puede ser `eod` o `stale`.
- `market_open` se elimina — no aplica a datos EOD.
- `last_updated` muestra la fecha del cierre: "Cierre DD/MM/YYYY".
- El endpoint `POST /market/refresh` se mantiene internamente pero no se expone en la UI.

### Componente: `EodMarketService`

**Ubicación:** `backend/app/modules/investments/market_data/eod_service.py`

**Responsabilidad única:** garantizar que al inicio de cada sesión de app haya datos de cierre del día anterior en caché DuckDB para todos los activos del catálogo.

**Flujo `ensure_today()`:**
1. Consultar caché DuckDB. Si existe un registro con `fetched_at` de fecha de hoy → devolver sin tocar la red.
2. Si no, iterar el catálogo de activos y llamar al `ProviderRouter` existente con `force_refresh=True` pero usando solo Stooq como provider efectivo (EOD nativo, sin API key).
3. Si Stooq falla para un activo → intentar Yahoo como último recurso (ya existe en el router).
4. Si ambos fallan → mantener el último cierre disponible en caché con `freshness_status = "stale"` y la fecha del dato registrada.

**TTL de caché:** 24 horas (sustituye los TTLs variables de 300–900s actuales por asset_type).

**Integración:** llamar a `EodMarketService.ensure_today()` en el `lifespan` de FastAPI (startup), en un thread separado para no bloquear el arranque.

### Cambios en `ProviderRouter`

- Añadir modo `eod_only: bool` que cuando es `True` excluye del fetch pool todos los providers excepto Stooq (y Yahoo como last resort). El ConsensusEngine, RequestBudget y fetch paralelo permanecen intactos para uso futuro (Fase 6 con IA podrá necesitar datos más ricos).
- El TTL override de 24h se aplica cuando se llama desde `EodMarketService`.

### Cambios en UI (frontend)

- **Eliminar** el botón "Actualizar" / "Refresh" de la pantalla Market Watch.
- **Reemplazar** `LiveIndicator` por un componente estático `EodBadge` que muestra "Cierre DD/MM/YYYY".
- **Eliminar** lógica de polling o refresh periódico en el hook de market data.
- La carga inicial es silenciosa (sin spinner bloqueante) — los datos se muestran cuando están disponibles en caché.

### Tests

| Archivo | Casos |
|---------|-------|
| `test_eod_service.py` | Cache hit mismo día (no llama red), cache miss (llama Stooq), Stooq falla → Yahoo, ambos fallan → stale, startup no bloquea |

---

## Parte 2 — Economic Intelligence Multi-Provider

### Objetivo

Ampliar el módulo de economic_data con tres providers adicionales (ECB, OECD, World Bank), un `EconomicProviderRouter` con lógica de autoridad por indicador, y nuevos indicadores en UI.

### Providers nuevos

#### `EcbProvider` (`economic_data/providers/ecb_provider.py`)

- **API:** ECB Data Warehouse (SDMX REST), sin API key.
- **Endpoint base:** `https://data-api.ecb.europa.eu/service/data/`
- **Series objetivo:**

| Series ID (ECB) | Indicador | Región |
|-----------------|-----------|--------|
| `ILM.M.U2.EUR.RF.IN.T.EUR.IR3.DAILY.NA` | Euríbor 3M | EA | ⚠️ verificar series ID exacto en implementación |
| `ILM.M.U2.EUR.RF.IN.T.EUR.IR1Y.DAILY.NA` | Euríbor 12M | EA | ⚠️ verificar series ID exacto en implementación |
| `ICP.M.U2.N.000000.4.ANR` | Inflación Eurozona HICP | EA |
| `ICP.M.ES.N.000000.4.ANR` | Inflación España HICP | ES |
| `FM.B.U2.EUR.FR.RF.EUR.FDFR.ST` | Tipo depósito BCE | EA |
| `BP.M.U2.W1.S1.S1.T.B.CA._Z.EUR.T.M` | Balanza cuenta corriente EA | EA |

- **Formato:** JSON SDMX-JSON v2. Parsear `dataSets[0].series` → extraer última observación disponible y la anterior.
- **Disponible sin API key** — si el endpoint responde 200, está disponible.

#### `OecdProvider` (`economic_data/providers/oecd_provider.py`)

- **API:** OECD Data API v2 (SDMX-JSON), sin API key.
- **Endpoint base:** `https://sdmx.oecd.org/public/rest/data/`
- **Series objetivo:**

| Dataset | Países | Indicador |
|---------|--------|-----------|
| `PRICES_CPI` | ES, EA, US | Inflación (validador) |
| `UNEMPLOYMENT_RATE` | ES, EA, US | Paro (validador) |
| `NAAG` | ES, EA, US | PIB real (validador) |

- Usar como **validador** (nunca como primario) — OECD tiene mayor lag de publicación que FRED/ECB.

#### `WorldBankProvider` (`economic_data/providers/worldbank_provider.py`)

- **API:** World Bank Open Data REST v2, sin API key.
- **Endpoint base:** `https://api.worldbank.org/v2/country/{iso}/indicator/{indicator}?format=json`
- **Países:** `ESP` (ES), `XC` (Eurozona), `USA` (US)
- **Indicadores:**

| WB Indicator | Nombre | Región | Frecuencia |
|--------------|--------|--------|------------|
| `GC.DOD.TOTL.GD.ZS` | Deuda/PIB (%) | ES, EA, US | Anual |
| `NY.GDP.PCAP.CD` | PIB per cápita (USD) | ES, EA, US | Anual |
| `SI.POV.GINI` | Índice Gini | ES, EA, US | Anual |

- Datos anuales → TTL de caché: 48h.

### Autoridad por indicador

```yaml
# economic_data_config.yaml
authority:
  ES:
    inflation:      primary: ecb,   validators: [oecd, fred]
    core_inflation: primary: fred,  validators: [oecd]
    unemployment:   primary: fred,  validators: [oecd]
    gdp:            primary: fred,  validators: [oecd, worldbank]
    bond_10y:       primary: stooq, validators: []
    euribor:        primary: ecb,   validators: [stooq]
  EA:
    inflation:      primary: ecb,   validators: [oecd, fred]
    core_inflation: primary: ecb,   validators: [fred]
    unemployment:   primary: fred,  validators: [oecd]
    gdp:            primary: fred,  validators: [oecd, worldbank]
    policy_rate:    primary: ecb,   validators: []
    bond_10y:       primary: stooq, validators: []
    euribor:        primary: ecb,   validators: [stooq]
    current_account: primary: ecb,  validators: []
  US:
    inflation:      primary: fred,  validators: [oecd]
    core_inflation: primary: fred,  validators: [oecd]
    unemployment:   primary: fred,  validators: [oecd]
    gdp:            primary: fred,  validators: [oecd, worldbank]
    policy_rate:    primary: fred,  validators: []
    bond_10y:       primary: stooq, validators: []
```

### Componente: `EconomicProviderRouter`

**Ubicación:** `economic_data/provider_router.py`

**Flujo por indicador:**
1. Llamar al provider primario.
2. Si responde → llamar a validadores en paralelo (`ThreadPoolExecutor`, timeout 8s).
3. Calcular `confidence_score`:
   - 1 provider: `0.7`
   - 2 providers dentro de ±0.5pp: `0.9`
   - 3+ providers dentro de ±0.5pp: `1.0`
   - Divergencia > ±0.5pp: penalizar `−0.2` por divergencia detectada
4. Si el primario falla → el primer validador disponible asciende, `source_fallback = true`.
5. Si todos fallan → devolver caché con `is_stale = true`.

**Campos nuevos en `IndicatorOut`:**
- `confidence_score: float` (0.0–1.0)
- `source_count: int` (cuántos providers devolvieron valor)
- `source_fallback: bool` (si el primario falló)

### Nuevos indicadores en UI

Añadir a `EconomyPage` en las tabs por región:

| Indicador | ES | EA | US |
|-----------|----|----|-----|
| Euríbor 3M | ✓ | ✓ | — |
| Euríbor 12M | ✓ | ✓ | — |
| Balanza c/c | — | ✓ | — |
| Deuda/PIB | ✓ | ✓ | ✓ |
| PIB per cápita | ✓ | ✓ | ✓ |

Cada indicador muestra un badge de confianza visual: verde (≥0.9), amarillo (≥0.7), rojo (<0.7).

### TTL por tipo de dato

| Frecuencia | TTL caché |
|------------|-----------|
| Diaria (euríbor, tipos) | 4h |
| Mensual (inflación, paro) | 24h |
| Trimestral (PIB) | 48h |
| Anual (World Bank) | 48h |

### Tests

| Archivo | Casos |
|---------|-------|
| `test_ecb_provider.py` | Serie correcta, sin datos, timeout, formato SDMX, fallback |
| `test_oecd_provider.py` | Serie correcta, sin datos, timeout, formato SDMX, fallback |
| `test_worldbank_provider.py` | Serie anual correcta, país no encontrado, timeout, datos vacíos |
| `test_economic_router.py` | Autoridad respetada, primario falla→fallback, confidence_score ≥2 fuentes, confidence_score divergencia, todos fallan→stale, World Bank datos anuales |

---

## Resumen de archivos nuevos/modificados

### Nuevos
- `backend/app/modules/investments/market_data/eod_service.py`
- `backend/app/modules/economic_data/providers/ecb_provider.py`
- `backend/app/modules/economic_data/providers/oecd_provider.py`
- `backend/app/modules/economic_data/providers/worldbank_provider.py`
- `backend/app/modules/economic_data/provider_router.py`
- `backend/app/modules/economic_data/economic_data_config.yaml`
- `backend/tests/test_eod_service.py`
- `backend/tests/test_ecb_provider.py`
- `backend/tests/test_oecd_provider.py`
- `backend/tests/test_worldbank_provider.py`
- `backend/tests/test_economic_router.py`

### Modificados
- `backend/app/modules/investments/market_data/router.py` — añadir `eod_only` mode
- `backend/app/main.py` — llamar `EodMarketService.ensure_today()` en lifespan startup
- `backend/app/modules/economic_data/service.py` — delegar a `EconomicProviderRouter`
- `backend/app/modules/economic_data/schemas.py` — añadir `confidence_score`, `source_count`, `source_fallback`
- `backend/app/modules/economic_data/repository.py` — añadir columnas nuevas si no existen
- `frontend/src/pages/MarketWatch` — eliminar botón refresh, añadir `EodBadge`
- `frontend/src/pages/Economy` — añadir nuevos indicadores y badge de confianza
- `docs/02_ROADMAP.md` — añadir Fase 4.7 y actualizar Fase 5

---

## Restricciones verificadas

- Ningún provider de pago — ECB, OECD, World Bank son completamente gratuitos y sin API key.
- No se almacenan datos personales en providers externos.
- La app funciona sin internet: devuelve caché stale con fecha visible.
- El LLM (Fase 6) no accede directamente a estas APIs — solo consume los endpoints internos ya normalizados.
