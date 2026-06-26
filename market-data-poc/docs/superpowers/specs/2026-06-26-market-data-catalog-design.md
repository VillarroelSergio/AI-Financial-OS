# Market Data Catalog — Diseño Fase 5.4.5

**Fecha:** 2026-06-26
**Fase:** 5.4.5
**Enfoque:** Catálogo como capa nueva, adapters sin tocar (Enfoque 2 — incremental)

---

## Contexto

La POC actual descarga todo lo que devuelve cada provider, generando ~11k registros donde el 96% son series IMF que nunca se usarán. El catálogo será el contrato central que define exactamente qué indicadores se obtienen, con qué frecuencia, de qué provider, y si son relevantes para Dashboard o IA.

Problema concreto en la última ejecución:
- IMF: 10.914 registros
- Resto de providers: ~374 registros combinados
- CSV resultante: inutilizable para DB y Dashboard

---

## Objetivo

Transformar el sistema de "agregador de providers" a "Market Data Platform" catalog-driven, manteniendo todos los adapters existentes funcionales durante la migración.

---

## Decisiones de diseño

| Decisión | Elección | Razón |
|---|---|---|
| Estructura del catálogo | Archivos YAML por categoría | Coincide con `adapters/spain/`, `adapters/usa/` etc. Fácil de extender. |
| Interfaz adapter | `fetch(indicator_id=None)` | Cambio mínimo. Legacy mode cuando `indicator_id=None`. |
| Alcance de esta fase | Catálogo + BDE SDMX + 5 CLI commands | BDE valida el patrón completo antes de migrar los 30+ adapters. |
| Modelos nuevos | Solo `CatalogIndicator` + `CatalogFetchResult` | YAGNI: la info de policy/visibility ya vive en `CatalogIndicator`. |

---

## Estructura de archivos nueva

```
market-data-poc/
└── catalog/
    ├── __init__.py          ← CatalogLoader
    ├── macro_spain.yaml
    ├── macro_europe.yaml
    ├── macro_usa.yaml
    ├── bonds.yaml
    ├── forex.yaml
    ├── indices.yaml
    ├── commodities.yaml
    ├── crypto.yaml
    └── news.yaml
```

---

## Schema YAML por indicador

```yaml
- id: euribor_3m
  name: "Euribor 3 meses"
  category: macro
  subcategory: interest_rates
  country: ES
  region: Spain
  frequency: daily
  priority: critical          # critical | high | medium | low
  dashboard: true
  ai: true
  historical: 10y             # 10y | 5y | 2y | 1y | 90d | 30d
  retention: 5y
  unit: "%"
  description: "Tipo de referencia hipotecas variables"
  provider_primary: bde
  provider_secondary: ecb
  provider_fallback: fred
```

Campos obligatorios: `id`, `name`, `category`, `country`, `frequency`, `priority`, `dashboard`, `ai`, `provider_primary`.
Campos opcionales: `provider_secondary`, `provider_fallback`, `subcategory`, `historical`, `retention`, `description`.

---

## Indicadores del catálogo

### macro_spain.yaml (priority: critical/high)
- `ipc_general` — IPC General España (INE → Eurostat → OECD)
- `ipc_subyacente` — IPC Subyacente (INE → Eurostat)
- `pib_spain` — PIB España (INE → World Bank → OECD)
- `desempleo_spain` — Tasa de paro (INE → Eurostat)
- `euribor_3m` — Euribor 3M (BDE → ECB → FRED)
- `euribor_12m` — Euribor 12M (BDE → ECB → FRED)
- `tipo_bce` — Tipo de interés BCE (ECB → FRED)
- `produccion_industrial_spain` — Producción industrial (INE → Eurostat)
- `pmi_manufacturero_spain` — PMI Manufacturero (medium)
- `pmi_servicios_spain` — PMI Servicios (medium)
- `confianza_consumidor_spain` — Confianza consumidor (medium)
- `deficit_spain` — Déficit público (Eurostat → OECD)
- `deuda_publica_spain` — Deuda pública % PIB (Eurostat → OECD)

### macro_europe.yaml
- `inflation_eurozone` — Inflación Eurozona (ECB → Eurostat)
- `gdp_eurozone` — PIB Eurozona (Eurostat → OECD)
- `unemployment_eurozone` — Desempleo Eurozona (Eurostat)
- `industrial_production_eurozone` — Producción industrial (Eurostat)
- `pmi_eurozone` — PMI Compuesto Eurozona (medium)
- `consumer_confidence_eurozone` — Confianza consumidor (EC → Eurostat)

### macro_usa.yaml
- `cpi_usa` — CPI USA (BLS → FRED)
- `core_cpi_usa` — Core CPI (BLS → FRED)
- `gdp_usa` — PIB USA (BEA → FRED → World Bank)
- `unemployment_usa` — Desempleo (BLS → FRED)
- `fed_funds_rate` — Fed Funds Rate (FRED)
- `nfp_usa` — Non-Farm Payrolls (BLS → FRED)
- `retail_sales_usa` — Ventas minoristas (Census → FRED)
- `housing_starts_usa` — Construcción de viviendas (Census → FRED)
- `industrial_production_usa` — Producción industrial (FRED)
- `consumer_sentiment_usa` — Confianza consumidor Michigan (FRED)
- `m2_usa` — Masa monetaria M2 (FRED)

### bonds.yaml
- `us_2y` — US Treasury 2Y (US Treasury → FRED)
- `us_5y` — US Treasury 5Y (US Treasury → FRED)
- `us_10y` — US Treasury 10Y (US Treasury → FRED)
- `us_30y` — US Treasury 30Y (US Treasury → FRED)
- `germany_10y` — Bund alemán 10Y (ECB → FRED)
- `spain_10y` — Bono español 10Y (BDE → ECB)

### forex.yaml
- `eur_usd` — EUR/USD (Frankfurter → ECB → Polygon)
- `eur_gbp` — EUR/GBP (Frankfurter → ECB)
- `eur_jpy` — EUR/JPY (Frankfurter → ECB)
- `eur_chf` — EUR/CHF (Frankfurter → ECB)
- `eur_cad` — EUR/CAD (Frankfurter → ECB)
- `eur_aud` — EUR/AUD (Frankfurter → ECB)
- `usd_jpy` — USD/JPY (Frankfurter → ECB)
- `gbp_usd` — GBP/USD (Frankfurter → ECB)

### indices.yaml
- `sp500` — S&P 500 (Stooq → Alpha Vantage → Polygon)
- `nasdaq` — Nasdaq Composite (Stooq → Alpha Vantage)
- `dow_jones` — Dow Jones (Stooq → Alpha Vantage)
- `russell_2000` — Russell 2000 (Stooq → Polygon)
- `ibex35` — IBEX 35 (BME → Stooq)
- `eurostoxx50` — EuroStoxx 50 (Stooq → ECB)
- `dax` — DAX (Stooq → Alpha Vantage)
- `cac40` — CAC 40 (Stooq → Alpha Vantage)
- `ftse100` — FTSE 100 (Stooq → Alpha Vantage)
- `nikkei225` — Nikkei 225 (Stooq → Alpha Vantage)

### commodities.yaml
- `gold` — Oro (Stooq → Alpha Vantage → Polygon)
- `silver` — Plata (Stooq → Alpha Vantage)
- `brent` — Brent Crude Oil (EIA → Stooq)
- `wti` — WTI Crude Oil (EIA → FRED)
- `natural_gas` — Gas Natural (EIA → Stooq)
- `uranium` — Uranio (Stooq, medium)
- `copper` — Cobre (Stooq → Alpha Vantage)
- `lithium` — Litio (Stooq, medium)

### crypto.yaml
- `bitcoin` — Bitcoin/USD (CoinGecko → Polygon)
- `ethereum` — Ethereum/USD (CoinGecko → Polygon)
- `solana` — Solana/USD (CoinGecko, low)
- `xrp` — XRP/USD (CoinGecko, low)

### news.yaml
- `news_macro` — Noticias macro (RSS → Finnhub)
- `news_markets` — Noticias mercados (RSS → Finnhub)
- `news_companies` — Noticias empresas (Finnhub → RSS)
- `news_technology` — Noticias tecnología (RSS)
- `news_central_banks` — Bancos centrales (RSS → ECB)

---

## CatalogLoader

`catalog/__init__.py` expone:

```python
class CatalogLoader:
    def load_all() -> list[CatalogIndicator]
    def get_by_id(id: str) -> CatalogIndicator | None
    def get_by_priority(*priorities: str) -> list[CatalogIndicator]
    def get_by_provider(provider_id: str) -> list[CatalogIndicator]
    def get_by_category(category: str) -> list[CatalogIndicator]
    def validate() -> list[str]   # retorna lista de errores
```

Valida en carga: campos obligatorios presentes, `provider_primary` existe en `providers.yaml`, `priority` es un valor válido, `frequency` es un valor válido.

---

## Cambios en BaseAdapter

```python
class BaseAdapter(ABC):
    supported_indicators: dict[str, dict] = {}  # nuevo campo de clase

    def fetch(self, indicator_id: str | None = None) -> AdapterResult:
        # Subclases migradas implementan lógica por indicator_id
        # Subclases legacy ignoran indicator_id (comportamiento actual)
        ...

    def supports(self, indicator_id: str) -> bool:
        return indicator_id in self.supported_indicators
```

---

## Cambios en ProviderOrchestrator

Nuevo método (no modifica el existente `fetch(capability)`):

```python
def fetch_indicator(self, indicator: CatalogIndicator) -> CatalogFetchResult:
    chain = [indicator.provider_primary, indicator.provider_secondary, indicator.provider_fallback]
    for provider_id in [p for p in chain if p]:
        adapter = self._get_adapter(provider_id)
        if adapter and adapter.supports(indicator.id):
            result = adapter.fetch(indicator.id)
            if result.success:
                return CatalogFetchResult(
                    indicator=indicator,
                    adapter_result=result,
                    provider_used=provider_id,
                    fallback_used=(provider_id != indicator.provider_primary),
                    catalog_id=indicator.id,
                )
    # Si ningún provider migrado soporta el indicador → legacy fallback
    return self._fetch_legacy(indicator)
```

El método `_fetch_legacy` llama al `fetch()` sin argumentos del primary provider — preserva comportamiento actual para indicadores no migrados.

---

## BDE adapter reescrito (primer adapter migrado)

```python
class BDEAdapter(BaseAdapter):
    supported_indicators = {
        "euribor_3m":  {"series": "BE0000001", "dataset": "TIPO"},
        "euribor_12m": {"series": "BE0000002", "dataset": "TIPO"},
        "tipo_bce":    {"series": "BE0000003", "dataset": "TIPO"},
        "spain_10y":   {"series": "BE0000004", "dataset": "BONO"},
    }

    def fetch(self, indicator_id=None):
        if indicator_id and indicator_id in self.supported_indicators:
            return self._fetch_sdmx(indicator_id)
        return self._fetch_legacy()   # HTML fallback actual

    def _fetch_sdmx(self, indicator_id):
        # SDMX REST API: https://www.bde.es/webbde/es/estadis/biest/...
        # Formato: XML o JSON SDMX
        # No parsear HTML
        ...
```

---

## Nuevos modelos

`models/catalog.py`:

```python
@dataclass
class CatalogIndicator:
    id: str
    name: str
    category: str
    subcategory: str
    country: str
    region: str
    frequency: str
    priority: str
    dashboard: bool
    ai: bool
    historical: str
    retention: str
    unit: str
    description: str
    provider_primary: str
    provider_secondary: str | None = None
    provider_fallback: str | None = None

@dataclass
class CatalogFetchResult:
    indicator: CatalogIndicator
    adapter_result: AdapterResult
    provider_used: str
    fallback_used: bool
    catalog_id: str
```

---

## CLI commands nuevos

```bash
# Tabla: id, name, priority, frequency, dashboard, ai, providers
python run_poc.py market:catalog

# Valida YAMLs: campos obligatorios, providers existentes, valores válidos
python run_poc.py market:catalog:validate

# Filtrado: --priority critical|high|medium|low --category --region
python run_poc.py market:catalog:list --priority critical

# Por indicador: provider primary, secondary, fallback, si está migrado
python run_poc.py market:catalog:coverage

# Fetch dirigido de todos los indicadores critical+high
# Output: CSV solo con indicadores del catálogo (~50-80 registros vs 11k)
python run_poc.py market:update
```

---

## Output CSV mejorado

Campos adicionales propagados desde el catálogo:

| Campo nuevo | Descripción |
|---|---|
| `catalog_id` | ID del indicador en el catálogo |
| `priority` | critical/high/medium/low |
| `dashboard` | true/false |
| `ai` | true/false |
| `provider_used` | Provider que realmente respondió |
| `fallback_used` | Si se usó fallback |

---

## Comparación entre providers

Cuando dos providers devuelven datos para el mismo `catalog_id`:
- Se conserva el registro con mayor `confidence_score`
- El descartado se loguea: provider, valor, diferencia porcentual
- `comparator.py` existente se reutiliza

---

## Market Catalog Report

Generado automáticamente tras `market:update` y `market:catalog:coverage`:

```
Market Catalog Report — 2026-06-26
====================================
Total indicadores:     52
Critical:              18   Dashboard: 45   AI: 38
High:                  21   Solo AI:    7   Solo Dashboard: 3
Medium:                10   Sin uso:    4
Low:                    3

Cobertura por provider:
  BDE (primary):        6 indicadores   Migrado: 4/6
  ECB (primary):        5 indicadores   Migrado: 0/5
  INE (primary):        5 indicadores   Migrado: 0/5
  ...

Gaps detectados:
  pmi_manufacturero_spain  → sin provider migrado
  lithium                  → Stooq intermitente
```

---

## Archivos modificados en esta fase

| Archivo | Acción |
|---|---|
| `catalog/__init__.py` | Nuevo — CatalogLoader |
| `catalog/macro_spain.yaml` | Nuevo |
| `catalog/macro_europe.yaml` | Nuevo |
| `catalog/macro_usa.yaml` | Nuevo |
| `catalog/bonds.yaml` | Nuevo |
| `catalog/forex.yaml` | Nuevo |
| `catalog/indices.yaml` | Nuevo |
| `catalog/commodities.yaml` | Nuevo |
| `catalog/crypto.yaml` | Nuevo |
| `catalog/news.yaml` | Nuevo |
| `models/catalog.py` | Nuevo |
| `adapters/spain/bde.py` | Reescribir (SDMX + legacy fallback) |
| `adapters/base.py` | Añadir `supported_indicators`, `fetch(indicator_id)` |
| `services/orchestrator.py` | Añadir `fetch_indicator()` |
| `run_poc.py` | Añadir 5 CLI commands + `market:update` flow |
| `exporters/csv_exporter.py` | Propagar `catalog_id`, `dashboard`, `ai`, `provider_used` |

Los 34 adapters no mencionados no se modifican en esta fase.

---

## Criterios de éxito

1. `market:catalog:validate` pasa sin errores
2. `market:catalog:coverage` muestra ≥52 indicadores
3. `market:update` produce CSV con ≤100 registros (vs 11k actuales)
4. `market:health` sigue funcionando igual (sin regresiones)
5. BDE retorna datos SDMX para `euribor_3m` sin parsear HTML
6. Fallback BDE → ECB funciona cuando BDE falla
