# Market Data Catalog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Añadir un catálogo de indicadores YAML que dirija exactamente qué descarga cada provider, reduciendo el CSV de ~11k registros a ≤100 registros precisos, con BDE migrado a SDMX como primer adapter validado.

**Architecture:** Enfoque incremental — `catalog/` se añade como capa nueva sin tocar los 34 adapters existentes. `BaseAdapter` recibe `supported_indicators` y `fetch(indicator_id=None)` con modo legacy cuando `indicator_id=None`. `ProviderOrchestrator` recibe nuevo método `fetch_indicator()` que usa el catálogo; el método `fetch(capability)` existente no se modifica.

**Tech Stack:** Python 3.14, requests, PyYAML, rich, pandas, dataclasses. Tests con pytest. Sin dependencias nuevas.

## Global Constraints

- Python 3.14 — usar `str | None` no `Optional[str]`
- Working directory: `d:/FinancialAgent/AI-Financial-OS/market-data-poc/`
- Virtualenv en `.venv/` — activar con `.venv/Scripts/activate` antes de ejecutar
- Ejecutar tests con: `python -m pytest tests/ -v`
- Ejecutar comandos POC con: `python run_poc.py <command>`
- No modificar adapters existentes salvo `adapters/spain/bde.py` y `adapters/base.py`
- `market:health` debe seguir funcionando igual tras cada tarea
- Prioridades válidas: `critical`, `high`, `medium`, `low`
- Frecuencias válidas: `realtime`, `daily`, `weekly`, `monthly`, `quarterly`, `yearly`
- Histórico válido: `10y`, `5y`, `2y`, `1y`, `90d`, `30d`
- IDs de provider válidos: los definidos en `config/providers.yaml` + `_EXTRA_PROVIDERS` en `run_poc.py`

---

## File Map

| Archivo | Acción | Responsabilidad |
|---|---|---|
| `models/catalog.py` | Crear | `CatalogIndicator`, `CatalogFetchResult` dataclasses |
| `catalog/__init__.py` | Crear | `CatalogLoader`: carga YAMLs, valida, filtra |
| `catalog/macro_spain.yaml` | Crear | 13 indicadores macro España |
| `catalog/macro_europe.yaml` | Crear | 6 indicadores macro Eurozona |
| `catalog/macro_usa.yaml` | Crear | 11 indicadores macro USA |
| `catalog/bonds.yaml` | Crear | 6 bonos soberanos |
| `catalog/forex.yaml` | Crear | 8 pares forex |
| `catalog/indices.yaml` | Crear | 10 índices bursátiles |
| `catalog/commodities.yaml` | Crear | 8 materias primas |
| `catalog/crypto.yaml` | Crear | 4 criptomonedas |
| `catalog/news.yaml` | Crear | 5 categorías de noticias |
| `adapters/base.py` | Modificar | Añadir `supported_indicators`, `supports()`, `fetch(indicator_id)` |
| `adapters/spain/bde.py` | Reescribir | SDMX para euribor/tipos, legacy fallback para resto |
| `services/orchestrator.py` | Modificar | Añadir `fetch_indicator()` y `_get_adapter()` |
| `exporters/csv_exporter.py` | Modificar | Soportar `CatalogFetchResult` con campos extra |
| `run_poc.py` | Modificar | Añadir 5 CLI commands + `market:update` flow |
| `tests/test_catalog.py` | Crear | Tests para CatalogLoader |
| `tests/test_catalog_orchestrator.py` | Crear | Tests para `fetch_indicator()` |
| `tests/test_bde_sdmx.py` | Crear | Tests para BDE SDMX adapter |

---

## Task 1: Modelos del catálogo

**Files:**
- Create: `models/catalog.py`
- Create: `tests/test_catalog_models.py`

**Interfaces:**
- Produce: `CatalogIndicator(id, name, category, subcategory, country, region, frequency, priority, dashboard, ai, historical, retention, unit, description, provider_primary, provider_secondary=None, provider_fallback=None)`
- Produce: `CatalogFetchResult(indicator: CatalogIndicator, adapter_result: AdapterResult, provider_used: str, fallback_used: bool, catalog_id: str)`

- [ ] **Step 1: Escribir tests de los modelos**

```python
# tests/test_catalog_models.py
from models.catalog import CatalogIndicator, CatalogFetchResult
from models.base import AdapterResult, ProviderMetadata
from datetime import datetime


def _make_metadata():
    return ProviderMetadata(
        name="Test", id="test", category="macro", region="Spain",
        method="api", base_url="", requires_api_key=False,
        declared_update_frequency="monthly", declared_historical_depth_years=5,
        license="open",
    )


def test_catalog_indicator_required_fields():
    ind = CatalogIndicator(
        id="euribor_3m", name="Euribor 3M", category="macro",
        subcategory="interest_rates", country="ES", region="Spain",
        frequency="daily", priority="critical", dashboard=True, ai=True,
        historical="10y", retention="5y", unit="%",
        description="Tipo de referencia", provider_primary="bde",
    )
    assert ind.id == "euribor_3m"
    assert ind.provider_secondary is None
    assert ind.provider_fallback is None


def test_catalog_indicator_optional_providers():
    ind = CatalogIndicator(
        id="eur_usd", name="EUR/USD", category="forex",
        subcategory="major_pairs", country="GLOBAL", region="Global",
        frequency="daily", priority="high", dashboard=True, ai=True,
        historical="5y", retention="2y", unit="rate", description="",
        provider_primary="frankfurter", provider_secondary="ecb",
        provider_fallback="polygon",
    )
    assert ind.provider_secondary == "ecb"
    assert ind.provider_fallback == "polygon"


def test_catalog_fetch_result():
    ind = CatalogIndicator(
        id="euribor_3m", name="Euribor 3M", category="macro",
        subcategory="interest_rates", country="ES", region="Spain",
        frequency="daily", priority="critical", dashboard=True, ai=True,
        historical="10y", retention="5y", unit="%", description="",
        provider_primary="bde",
    )
    result = AdapterResult(
        provider="BDE", success=True, records=[], error=None,
        latency_ms=100.0, raw_sample=None, metadata=_make_metadata(),
    )
    cfr = CatalogFetchResult(
        indicator=ind, adapter_result=result,
        provider_used="bde", fallback_used=False, catalog_id="euribor_3m",
    )
    assert cfr.catalog_id == "euribor_3m"
    assert cfr.fallback_used is False
```

- [ ] **Step 2: Ejecutar tests para verificar que fallan**

```
python -m pytest tests/test_catalog_models.py -v
```
Expected: `ImportError: cannot import name 'CatalogIndicator' from 'models.catalog'`

- [ ] **Step 3: Crear `models/catalog.py`**

```python
from dataclasses import dataclass
from models.base import AdapterResult


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

- [ ] **Step 4: Ejecutar tests**

```
python -m pytest tests/test_catalog_models.py -v
```
Expected: `3 passed`

- [ ] **Step 5: Verificar que `market:health` sigue funcionando**

```
python run_poc.py market:health
```
Expected: tabla de health igual que antes.

- [ ] **Step 6: Commit**

```bash
git add models/catalog.py tests/test_catalog_models.py
git commit -m "feat: add CatalogIndicator and CatalogFetchResult models"
```

---

## Task 2: Archivos YAML del catálogo

**Files:**
- Create: `catalog/macro_spain.yaml`
- Create: `catalog/macro_europe.yaml`
- Create: `catalog/macro_usa.yaml`
- Create: `catalog/bonds.yaml`
- Create: `catalog/forex.yaml`
- Create: `catalog/indices.yaml`
- Create: `catalog/commodities.yaml`
- Create: `catalog/crypto.yaml`
- Create: `catalog/news.yaml`

**Interfaces:**
- Consumes: nada
- Produce: 9 archivos YAML con schema `{id, name, category, subcategory, country, region, frequency, priority, dashboard, ai, historical, retention, unit, description, provider_primary, provider_secondary?, provider_fallback?}`

- [ ] **Step 1: Crear `catalog/macro_spain.yaml`**

```yaml
- id: ipc_general
  name: "IPC General España"
  category: macro
  subcategory: inflation
  country: ES
  region: Spain
  frequency: monthly
  priority: critical
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "%"
  description: "Índice de Precios al Consumo general"
  provider_primary: ine
  provider_secondary: eurostat
  provider_fallback: oecd

- id: ipc_subyacente
  name: "IPC Subyacente España"
  category: macro
  subcategory: inflation
  country: ES
  region: Spain
  frequency: monthly
  priority: high
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "%"
  description: "IPC excluida energía y alimentos no elaborados"
  provider_primary: ine
  provider_secondary: eurostat

- id: pib_spain
  name: "PIB España"
  category: macro
  subcategory: gdp
  country: ES
  region: Spain
  frequency: quarterly
  priority: critical
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "EUR bn"
  description: "Producto Interior Bruto España"
  provider_primary: ine
  provider_secondary: world_bank
  provider_fallback: oecd

- id: desempleo_spain
  name: "Tasa de Desempleo España"
  category: macro
  subcategory: employment
  country: ES
  region: Spain
  frequency: monthly
  priority: critical
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "%"
  description: "Tasa de paro EPA"
  provider_primary: ine
  provider_secondary: eurostat

- id: euribor_3m
  name: "Euribor 3 meses"
  category: macro
  subcategory: interest_rates
  country: ES
  region: Spain
  frequency: daily
  priority: critical
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "%"
  description: "Tipo de referencia hipotecas variables"
  provider_primary: bde
  provider_secondary: ecb
  provider_fallback: fred

- id: euribor_12m
  name: "Euribor 12 meses"
  category: macro
  subcategory: interest_rates
  country: ES
  region: Spain
  frequency: daily
  priority: critical
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "%"
  description: "Tipo de referencia hipotecas anuales"
  provider_primary: bde
  provider_secondary: ecb
  provider_fallback: fred

- id: tipo_bce
  name: "Tipo de interés BCE"
  category: macro
  subcategory: interest_rates
  country: EA
  region: Eurozone
  frequency: monthly
  priority: critical
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "%"
  description: "Tipo de interés de referencia del BCE"
  provider_primary: ecb
  provider_secondary: fred

- id: produccion_industrial_spain
  name: "Producción Industrial España"
  category: macro
  subcategory: industrial
  country: ES
  region: Spain
  frequency: monthly
  priority: high
  dashboard: true
  ai: true
  historical: 5y
  retention: 3y
  unit: "index"
  description: "Índice de producción industrial"
  provider_primary: ine
  provider_secondary: eurostat

- id: pmi_manufacturero_spain
  name: "PMI Manufacturero España"
  category: macro
  subcategory: pmi
  country: ES
  region: Spain
  frequency: monthly
  priority: medium
  dashboard: true
  ai: true
  historical: 5y
  retention: 2y
  unit: "index"
  description: "Purchasing Managers Index manufacturero"
  provider_primary: ine

- id: pmi_servicios_spain
  name: "PMI Servicios España"
  category: macro
  subcategory: pmi
  country: ES
  region: Spain
  frequency: monthly
  priority: medium
  dashboard: true
  ai: true
  historical: 5y
  retention: 2y
  unit: "index"
  description: "Purchasing Managers Index servicios"
  provider_primary: ine

- id: confianza_consumidor_spain
  name: "Confianza del Consumidor España"
  category: macro
  subcategory: sentiment
  country: ES
  region: Spain
  frequency: monthly
  priority: medium
  dashboard: true
  ai: true
  historical: 5y
  retention: 2y
  unit: "index"
  description: "Índice de confianza del consumidor"
  provider_primary: european_commission
  provider_secondary: eurostat

- id: deficit_spain
  name: "Déficit Público España"
  category: macro
  subcategory: fiscal
  country: ES
  region: Spain
  frequency: quarterly
  priority: high
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "% PIB"
  description: "Déficit de las AAPP en % del PIB"
  provider_primary: eurostat
  provider_secondary: oecd

- id: deuda_publica_spain
  name: "Deuda Pública España"
  category: macro
  subcategory: fiscal
  country: ES
  region: Spain
  frequency: quarterly
  priority: high
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "% PIB"
  description: "Deuda pública en % del PIB"
  provider_primary: eurostat
  provider_secondary: oecd
```

- [ ] **Step 2: Crear `catalog/macro_europe.yaml`**

```yaml
- id: inflation_eurozone
  name: "Inflación Eurozona"
  category: macro
  subcategory: inflation
  country: EA
  region: Eurozone
  frequency: monthly
  priority: critical
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "%"
  description: "HICP inflación Eurozona"
  provider_primary: ecb
  provider_secondary: eurostat

- id: gdp_eurozone
  name: "PIB Eurozona"
  category: macro
  subcategory: gdp
  country: EA
  region: Eurozone
  frequency: quarterly
  priority: critical
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "EUR bn"
  description: "Producto Interior Bruto Eurozona"
  provider_primary: eurostat
  provider_secondary: oecd

- id: unemployment_eurozone
  name: "Desempleo Eurozona"
  category: macro
  subcategory: employment
  country: EA
  region: Eurozone
  frequency: monthly
  priority: high
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "%"
  description: "Tasa de desempleo Eurozona"
  provider_primary: eurostat

- id: industrial_production_eurozone
  name: "Producción Industrial Eurozona"
  category: macro
  subcategory: industrial
  country: EA
  region: Eurozone
  frequency: monthly
  priority: high
  dashboard: true
  ai: true
  historical: 5y
  retention: 3y
  unit: "index"
  description: "Índice producción industrial Eurozona"
  provider_primary: eurostat

- id: pmi_eurozone
  name: "PMI Compuesto Eurozona"
  category: macro
  subcategory: pmi
  country: EA
  region: Eurozone
  frequency: monthly
  priority: medium
  dashboard: true
  ai: true
  historical: 5y
  retention: 2y
  unit: "index"
  description: "PMI compuesto manufacturero + servicios"
  provider_primary: eurostat

- id: consumer_confidence_eurozone
  name: "Confianza Consumidor Eurozona"
  category: macro
  subcategory: sentiment
  country: EA
  region: Eurozone
  frequency: monthly
  priority: medium
  dashboard: true
  ai: true
  historical: 5y
  retention: 2y
  unit: "index"
  description: "Índice de confianza del consumidor europeo"
  provider_primary: european_commission
  provider_secondary: eurostat
```

- [ ] **Step 3: Crear `catalog/macro_usa.yaml`**

```yaml
- id: cpi_usa
  name: "CPI USA"
  category: macro
  subcategory: inflation
  country: US
  region: USA
  frequency: monthly
  priority: critical
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "%"
  description: "Consumer Price Index USA"
  provider_primary: bls
  provider_secondary: fred

- id: core_cpi_usa
  name: "Core CPI USA"
  category: macro
  subcategory: inflation
  country: US
  region: USA
  frequency: monthly
  priority: critical
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "%"
  description: "CPI excluida energía y alimentos"
  provider_primary: bls
  provider_secondary: fred

- id: gdp_usa
  name: "PIB USA"
  category: macro
  subcategory: gdp
  country: US
  region: USA
  frequency: quarterly
  priority: critical
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "USD bn"
  description: "Gross Domestic Product USA"
  provider_primary: bea
  provider_secondary: fred
  provider_fallback: world_bank

- id: unemployment_usa
  name: "Desempleo USA"
  category: macro
  subcategory: employment
  country: US
  region: USA
  frequency: monthly
  priority: critical
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "%"
  description: "Unemployment rate USA"
  provider_primary: bls
  provider_secondary: fred

- id: fed_funds_rate
  name: "Fed Funds Rate"
  category: macro
  subcategory: interest_rates
  country: US
  region: USA
  frequency: monthly
  priority: critical
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "%"
  description: "Tipo de interés de referencia de la Fed"
  provider_primary: fred

- id: nfp_usa
  name: "Non-Farm Payrolls USA"
  category: macro
  subcategory: employment
  country: US
  region: USA
  frequency: monthly
  priority: high
  dashboard: true
  ai: true
  historical: 5y
  retention: 3y
  unit: "thousands"
  description: "Nóminas no agrícolas"
  provider_primary: bls
  provider_secondary: fred

- id: retail_sales_usa
  name: "Retail Sales USA"
  category: macro
  subcategory: consumption
  country: US
  region: USA
  frequency: monthly
  priority: high
  dashboard: true
  ai: true
  historical: 5y
  retention: 3y
  unit: "USD mn"
  description: "Ventas al por menor"
  provider_primary: census
  provider_secondary: fred

- id: housing_starts_usa
  name: "Housing Starts USA"
  category: macro
  subcategory: housing
  country: US
  region: USA
  frequency: monthly
  priority: high
  dashboard: true
  ai: true
  historical: 5y
  retention: 3y
  unit: "thousands"
  description: "Inicio de construcción de viviendas"
  provider_primary: census
  provider_secondary: fred

- id: industrial_production_usa
  name: "Producción Industrial USA"
  category: macro
  subcategory: industrial
  country: US
  region: USA
  frequency: monthly
  priority: high
  dashboard: true
  ai: true
  historical: 5y
  retention: 3y
  unit: "index"
  description: "Índice de producción industrial USA"
  provider_primary: fred

- id: consumer_sentiment_usa
  name: "Consumer Sentiment USA"
  category: macro
  subcategory: sentiment
  country: US
  region: USA
  frequency: monthly
  priority: medium
  dashboard: true
  ai: true
  historical: 5y
  retention: 2y
  unit: "index"
  description: "University of Michigan Consumer Sentiment"
  provider_primary: fred

- id: m2_usa
  name: "M2 Money Supply USA"
  category: macro
  subcategory: monetary
  country: US
  region: USA
  frequency: monthly
  priority: medium
  dashboard: false
  ai: true
  historical: 10y
  retention: 5y
  unit: "USD bn"
  description: "Masa monetaria M2"
  provider_primary: fred
```

- [ ] **Step 4: Crear `catalog/bonds.yaml`**

```yaml
- id: us_2y
  name: "US Treasury 2Y"
  category: bonds
  subcategory: government
  country: US
  region: USA
  frequency: daily
  priority: critical
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "%"
  description: "Rendimiento bono del Tesoro USA 2 años"
  provider_primary: treasury
  provider_secondary: fred

- id: us_5y
  name: "US Treasury 5Y"
  category: bonds
  subcategory: government
  country: US
  region: USA
  frequency: daily
  priority: high
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "%"
  description: "Rendimiento bono del Tesoro USA 5 años"
  provider_primary: treasury
  provider_secondary: fred

- id: us_10y
  name: "US Treasury 10Y"
  category: bonds
  subcategory: government
  country: US
  region: USA
  frequency: daily
  priority: critical
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "%"
  description: "Rendimiento bono del Tesoro USA 10 años"
  provider_primary: treasury
  provider_secondary: fred

- id: us_30y
  name: "US Treasury 30Y"
  category: bonds
  subcategory: government
  country: US
  region: USA
  frequency: daily
  priority: high
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "%"
  description: "Rendimiento bono del Tesoro USA 30 años"
  provider_primary: treasury
  provider_secondary: fred

- id: germany_10y
  name: "Bund Alemán 10Y"
  category: bonds
  subcategory: government
  country: DE
  region: Eurozone
  frequency: daily
  priority: critical
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "%"
  description: "Rendimiento Bund alemán 10 años"
  provider_primary: ecb
  provider_secondary: fred

- id: spain_10y
  name: "Bono Español 10Y"
  category: bonds
  subcategory: government
  country: ES
  region: Spain
  frequency: daily
  priority: critical
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "%"
  description: "Rendimiento bono del Estado español 10 años"
  provider_primary: bde
  provider_secondary: ecb
```

- [ ] **Step 5: Crear `catalog/forex.yaml`**

```yaml
- id: eur_usd
  name: "EUR/USD"
  category: forex
  subcategory: major_pairs
  country: GLOBAL
  region: Global
  frequency: daily
  priority: critical
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "rate"
  description: "Par Euro / Dólar estadounidense"
  provider_primary: frankfurter
  provider_secondary: ecb
  provider_fallback: polygon

- id: eur_gbp
  name: "EUR/GBP"
  category: forex
  subcategory: major_pairs
  country: GLOBAL
  region: Global
  frequency: daily
  priority: high
  dashboard: true
  ai: true
  historical: 5y
  retention: 3y
  unit: "rate"
  description: "Par Euro / Libra esterlina"
  provider_primary: frankfurter
  provider_secondary: ecb

- id: eur_jpy
  name: "EUR/JPY"
  category: forex
  subcategory: major_pairs
  country: GLOBAL
  region: Global
  frequency: daily
  priority: high
  dashboard: true
  ai: true
  historical: 5y
  retention: 3y
  unit: "rate"
  description: "Par Euro / Yen japonés"
  provider_primary: frankfurter
  provider_secondary: ecb

- id: eur_chf
  name: "EUR/CHF"
  category: forex
  subcategory: major_pairs
  country: GLOBAL
  region: Global
  frequency: daily
  priority: high
  dashboard: true
  ai: true
  historical: 5y
  retention: 3y
  unit: "rate"
  description: "Par Euro / Franco suizo"
  provider_primary: frankfurter
  provider_secondary: ecb

- id: eur_cad
  name: "EUR/CAD"
  category: forex
  subcategory: major_pairs
  country: GLOBAL
  region: Global
  frequency: daily
  priority: medium
  dashboard: true
  ai: false
  historical: 5y
  retention: 2y
  unit: "rate"
  description: "Par Euro / Dólar canadiense"
  provider_primary: frankfurter
  provider_secondary: ecb

- id: eur_aud
  name: "EUR/AUD"
  category: forex
  subcategory: major_pairs
  country: GLOBAL
  region: Global
  frequency: daily
  priority: medium
  dashboard: true
  ai: false
  historical: 5y
  retention: 2y
  unit: "rate"
  description: "Par Euro / Dólar australiano"
  provider_primary: frankfurter
  provider_secondary: ecb

- id: usd_jpy
  name: "USD/JPY"
  category: forex
  subcategory: major_pairs
  country: GLOBAL
  region: Global
  frequency: daily
  priority: high
  dashboard: true
  ai: true
  historical: 5y
  retention: 3y
  unit: "rate"
  description: "Par Dólar estadounidense / Yen japonés"
  provider_primary: frankfurter
  provider_secondary: ecb

- id: gbp_usd
  name: "GBP/USD"
  category: forex
  subcategory: major_pairs
  country: GLOBAL
  region: Global
  frequency: daily
  priority: high
  dashboard: true
  ai: true
  historical: 5y
  retention: 3y
  unit: "rate"
  description: "Par Libra esterlina / Dólar estadounidense"
  provider_primary: frankfurter
  provider_secondary: ecb
```

- [ ] **Step 6: Crear `catalog/indices.yaml`**

```yaml
- id: sp500
  name: "S&P 500"
  category: indices
  subcategory: usa
  country: US
  region: USA
  frequency: daily
  priority: critical
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "index"
  description: "Standard & Poor's 500"
  provider_primary: stooq
  provider_secondary: alpha_vantage
  provider_fallback: polygon

- id: nasdaq
  name: "Nasdaq Composite"
  category: indices
  subcategory: usa
  country: US
  region: USA
  frequency: daily
  priority: critical
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "index"
  description: "Nasdaq Composite Index"
  provider_primary: stooq
  provider_secondary: alpha_vantage

- id: dow_jones
  name: "Dow Jones Industrial"
  category: indices
  subcategory: usa
  country: US
  region: USA
  frequency: daily
  priority: high
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "index"
  description: "Dow Jones Industrial Average"
  provider_primary: stooq
  provider_secondary: alpha_vantage

- id: russell_2000
  name: "Russell 2000"
  category: indices
  subcategory: usa
  country: US
  region: USA
  frequency: daily
  priority: medium
  dashboard: true
  ai: true
  historical: 5y
  retention: 3y
  unit: "index"
  description: "Russell 2000 small cap index"
  provider_primary: stooq
  provider_secondary: polygon

- id: ibex35
  name: "IBEX 35"
  category: indices
  subcategory: spain
  country: ES
  region: Spain
  frequency: daily
  priority: critical
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "index"
  description: "Índice bursátil español IBEX 35"
  provider_primary: bme
  provider_secondary: stooq

- id: eurostoxx50
  name: "EuroStoxx 50"
  category: indices
  subcategory: europe
  country: EA
  region: Eurozone
  frequency: daily
  priority: critical
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "index"
  description: "Índice paneuropeo EuroStoxx 50"
  provider_primary: stooq
  provider_secondary: ecb

- id: dax
  name: "DAX"
  category: indices
  subcategory: europe
  country: DE
  region: Eurozone
  frequency: daily
  priority: high
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "index"
  description: "Índice bursátil alemán DAX"
  provider_primary: stooq
  provider_secondary: alpha_vantage

- id: cac40
  name: "CAC 40"
  category: indices
  subcategory: europe
  country: FR
  region: Eurozone
  frequency: daily
  priority: high
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "index"
  description: "Índice bursátil francés CAC 40"
  provider_primary: stooq
  provider_secondary: alpha_vantage

- id: ftse100
  name: "FTSE 100"
  category: indices
  subcategory: europe
  country: GB
  region: Global
  frequency: daily
  priority: high
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "index"
  description: "Índice bursátil británico FTSE 100"
  provider_primary: stooq
  provider_secondary: alpha_vantage

- id: nikkei225
  name: "Nikkei 225"
  category: indices
  subcategory: asia
  country: JP
  region: Global
  frequency: daily
  priority: high
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "index"
  description: "Índice bursátil japonés Nikkei 225"
  provider_primary: stooq
  provider_secondary: alpha_vantage
```

- [ ] **Step 7: Crear `catalog/commodities.yaml`**

```yaml
- id: gold
  name: "Oro"
  category: commodities
  subcategory: precious_metals
  country: GLOBAL
  region: Global
  frequency: daily
  priority: critical
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "USD/oz"
  description: "Precio del oro por onza troy"
  provider_primary: stooq
  provider_secondary: alpha_vantage
  provider_fallback: polygon

- id: silver
  name: "Plata"
  category: commodities
  subcategory: precious_metals
  country: GLOBAL
  region: Global
  frequency: daily
  priority: high
  dashboard: true
  ai: true
  historical: 5y
  retention: 3y
  unit: "USD/oz"
  description: "Precio de la plata por onza troy"
  provider_primary: stooq
  provider_secondary: alpha_vantage

- id: brent
  name: "Brent Crude Oil"
  category: commodities
  subcategory: energy
  country: GLOBAL
  region: Global
  frequency: daily
  priority: critical
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "USD/bbl"
  description: "Precio del petróleo Brent"
  provider_primary: eia
  provider_secondary: stooq

- id: wti
  name: "WTI Crude Oil"
  category: commodities
  subcategory: energy
  country: US
  region: USA
  frequency: daily
  priority: critical
  dashboard: true
  ai: true
  historical: 10y
  retention: 5y
  unit: "USD/bbl"
  description: "West Texas Intermediate crude oil"
  provider_primary: eia
  provider_secondary: fred

- id: natural_gas
  name: "Gas Natural"
  category: commodities
  subcategory: energy
  country: GLOBAL
  region: Global
  frequency: daily
  priority: high
  dashboard: true
  ai: true
  historical: 5y
  retention: 3y
  unit: "USD/MMBtu"
  description: "Precio del gas natural"
  provider_primary: eia
  provider_secondary: stooq

- id: uranium
  name: "Uranio"
  category: commodities
  subcategory: energy
  country: GLOBAL
  region: Global
  frequency: weekly
  priority: medium
  dashboard: true
  ai: false
  historical: 5y
  retention: 2y
  unit: "USD/lb"
  description: "Precio del uranio"
  provider_primary: stooq

- id: copper
  name: "Cobre"
  category: commodities
  subcategory: base_metals
  country: GLOBAL
  region: Global
  frequency: daily
  priority: high
  dashboard: true
  ai: true
  historical: 5y
  retention: 3y
  unit: "USD/lb"
  description: "Precio del cobre"
  provider_primary: stooq
  provider_secondary: alpha_vantage

- id: lithium
  name: "Litio"
  category: commodities
  subcategory: base_metals
  country: GLOBAL
  region: Global
  frequency: weekly
  priority: medium
  dashboard: true
  ai: false
  historical: 5y
  retention: 2y
  unit: "USD/t"
  description: "Precio del litio"
  provider_primary: stooq
```

- [ ] **Step 8: Crear `catalog/crypto.yaml`**

```yaml
- id: bitcoin
  name: "Bitcoin"
  category: crypto
  subcategory: major
  country: GLOBAL
  region: Global
  frequency: daily
  priority: high
  dashboard: true
  ai: true
  historical: 5y
  retention: 3y
  unit: "USD"
  description: "Bitcoin precio en USD"
  provider_primary: coingecko
  provider_secondary: polygon

- id: ethereum
  name: "Ethereum"
  category: crypto
  subcategory: major
  country: GLOBAL
  region: Global
  frequency: daily
  priority: high
  dashboard: true
  ai: true
  historical: 5y
  retention: 3y
  unit: "USD"
  description: "Ethereum precio en USD"
  provider_primary: coingecko
  provider_secondary: polygon

- id: solana
  name: "Solana"
  category: crypto
  subcategory: altcoin
  country: GLOBAL
  region: Global
  frequency: daily
  priority: low
  dashboard: false
  ai: false
  historical: 2y
  retention: 1y
  unit: "USD"
  description: "Solana precio en USD"
  provider_primary: coingecko

- id: xrp
  name: "XRP"
  category: crypto
  subcategory: altcoin
  country: GLOBAL
  region: Global
  frequency: daily
  priority: low
  dashboard: false
  ai: false
  historical: 2y
  retention: 1y
  unit: "USD"
  description: "XRP precio en USD"
  provider_primary: coingecko
```

- [ ] **Step 9: Crear `catalog/news.yaml`**

```yaml
- id: news_macro
  name: "Noticias Macro"
  category: news
  subcategory: macro
  country: GLOBAL
  region: Global
  frequency: realtime
  priority: high
  dashboard: true
  ai: true
  historical: 30d
  retention: 90d
  unit: "text"
  description: "Noticias macroeconómicas"
  provider_primary: rss
  provider_secondary: finnhub

- id: news_markets
  name: "Noticias Mercados"
  category: news
  subcategory: markets
  country: GLOBAL
  region: Global
  frequency: realtime
  priority: high
  dashboard: true
  ai: true
  historical: 30d
  retention: 90d
  unit: "text"
  description: "Noticias de mercados financieros"
  provider_primary: rss
  provider_secondary: finnhub

- id: news_companies
  name: "Noticias Empresas"
  category: news
  subcategory: companies
  country: GLOBAL
  region: Global
  frequency: realtime
  priority: medium
  dashboard: true
  ai: true
  historical: 30d
  retention: 90d
  unit: "text"
  description: "Noticias corporativas"
  provider_primary: finnhub
  provider_secondary: rss

- id: news_technology
  name: "Noticias Tecnología"
  category: news
  subcategory: technology
  country: GLOBAL
  region: Global
  frequency: realtime
  priority: medium
  dashboard: false
  ai: true
  historical: 30d
  retention: 30d
  unit: "text"
  description: "Noticias de tecnología"
  provider_primary: rss

- id: news_central_banks
  name: "Bancos Centrales"
  category: news
  subcategory: central_banks
  country: GLOBAL
  region: Global
  frequency: realtime
  priority: high
  dashboard: true
  ai: true
  historical: 30d
  retention: 90d
  unit: "text"
  description: "Comunicados y noticias de bancos centrales"
  provider_primary: rss
  provider_secondary: ecb
```

- [ ] **Step 10: Verificar que los YAMLs son válidos**

```bash
python -c "
import yaml, pathlib
for f in pathlib.Path('catalog').glob('*.yaml'):
    data = yaml.safe_load(f.read_text(encoding='utf-8'))
    print(f'{f.name}: {len(data)} indicators')
"
```
Expected: 9 líneas, cada una con el nombre del archivo y el número de indicadores. Total ≥52.

- [ ] **Step 11: Commit**

```bash
git add catalog/
git commit -m "feat: add catalog YAML files with 52+ indicators across 9 categories"
```

---

## Task 3: CatalogLoader

**Files:**
- Create: `catalog/__init__.py`
- Create: `tests/test_catalog.py`

**Interfaces:**
- Consumes: `models/catalog.py::CatalogIndicator`, archivos `catalog/*.yaml`
- Produce: `CatalogLoader` con métodos `load_all()`, `get_by_id(id)`, `get_by_priority(*priorities)`, `get_by_provider(provider_id)`, `get_by_category(category)`, `validate() -> list[str]`

- [ ] **Step 1: Escribir tests**

```python
# tests/test_catalog.py
import pytest
from catalog import CatalogLoader


def test_load_all_returns_all_indicators():
    loader = CatalogLoader()
    indicators = loader.load_all()
    assert len(indicators) >= 52


def test_get_by_id_found():
    loader = CatalogLoader()
    ind = loader.get_by_id("euribor_3m")
    assert ind is not None
    assert ind.id == "euribor_3m"
    assert ind.provider_primary == "bde"


def test_get_by_id_not_found():
    loader = CatalogLoader()
    assert loader.get_by_id("nonexistent_indicator") is None


def test_get_by_priority_critical():
    loader = CatalogLoader()
    critical = loader.get_by_priority("critical")
    assert len(critical) >= 10
    assert all(i.priority == "critical" for i in critical)


def test_get_by_priority_multiple():
    loader = CatalogLoader()
    high_and_critical = loader.get_by_priority("critical", "high")
    assert len(high_and_critical) >= 25
    assert all(i.priority in ("critical", "high") for i in high_and_critical)


def test_get_by_provider():
    loader = CatalogLoader()
    bde_indicators = loader.get_by_provider("bde")
    assert len(bde_indicators) >= 2
    ids = [i.id for i in bde_indicators]
    assert "euribor_3m" in ids


def test_get_by_category():
    loader = CatalogLoader()
    forex = loader.get_by_category("forex")
    assert len(forex) == 8
    assert all(i.category == "forex" for i in forex)


def test_validate_no_errors():
    loader = CatalogLoader()
    errors = loader.validate()
    assert errors == [], f"Validation errors: {errors}"


def test_all_have_required_fields():
    loader = CatalogLoader()
    for ind in loader.load_all():
        assert ind.id, f"Missing id in {ind}"
        assert ind.name, f"Missing name in {ind}"
        assert ind.provider_primary, f"Missing provider_primary in {ind.id}"
        assert ind.priority in ("critical", "high", "medium", "low"), \
            f"Invalid priority '{ind.priority}' in {ind.id}"
        assert ind.frequency in ("realtime", "daily", "weekly", "monthly", "quarterly", "yearly"), \
            f"Invalid frequency '{ind.frequency}' in {ind.id}"
```

- [ ] **Step 2: Ejecutar tests para verificar que fallan**

```
python -m pytest tests/test_catalog.py -v
```
Expected: `ImportError: cannot import name 'CatalogLoader' from 'catalog'`

- [ ] **Step 3: Crear `catalog/__init__.py`**

```python
from pathlib import Path
from typing import Any
import yaml
from models.catalog import CatalogIndicator

_CATALOG_DIR = Path(__file__).parent
_VALID_PRIORITIES = {"critical", "high", "medium", "low"}
_VALID_FREQUENCIES = {"realtime", "daily", "weekly", "monthly", "quarterly", "yearly"}
_VALID_HISTORICAL = {"10y", "5y", "2y", "1y", "90d", "30d"}


class CatalogLoader:
    def __init__(self, catalog_dir: Path | None = None):
        self._dir = catalog_dir or _CATALOG_DIR
        self._cache: list[CatalogIndicator] | None = None

    def load_all(self) -> list[CatalogIndicator]:
        if self._cache is not None:
            return self._cache
        indicators: list[CatalogIndicator] = []
        for yaml_file in sorted(self._dir.glob("*.yaml")):
            raw: list[dict[str, Any]] = yaml.safe_load(yaml_file.read_text(encoding="utf-8")) or []
            for entry in raw:
                indicators.append(self._parse(entry))
        self._cache = indicators
        return indicators

    def get_by_id(self, indicator_id: str) -> CatalogIndicator | None:
        return next((i for i in self.load_all() if i.id == indicator_id), None)

    def get_by_priority(self, *priorities: str) -> list[CatalogIndicator]:
        return [i for i in self.load_all() if i.priority in priorities]

    def get_by_provider(self, provider_id: str) -> list[CatalogIndicator]:
        return [
            i for i in self.load_all()
            if provider_id in (i.provider_primary, i.provider_secondary, i.provider_fallback)
        ]

    def get_by_category(self, category: str) -> list[CatalogIndicator]:
        return [i for i in self.load_all() if i.category == category]

    def validate(self) -> list[str]:
        errors: list[str] = []
        seen_ids: set[str] = set()
        for ind in self.load_all():
            if not ind.id:
                errors.append("Indicator missing id")
            elif ind.id in seen_ids:
                errors.append(f"Duplicate id: {ind.id}")
            else:
                seen_ids.add(ind.id)
            if not ind.name:
                errors.append(f"{ind.id}: missing name")
            if not ind.provider_primary:
                errors.append(f"{ind.id}: missing provider_primary")
            if ind.priority not in _VALID_PRIORITIES:
                errors.append(f"{ind.id}: invalid priority '{ind.priority}'")
            if ind.frequency not in _VALID_FREQUENCIES:
                errors.append(f"{ind.id}: invalid frequency '{ind.frequency}'")
        return errors

    @staticmethod
    def _parse(entry: dict[str, Any]) -> CatalogIndicator:
        return CatalogIndicator(
            id=entry["id"],
            name=entry["name"],
            category=entry.get("category", ""),
            subcategory=entry.get("subcategory", ""),
            country=entry.get("country", "GLOBAL"),
            region=entry.get("region", "Global"),
            frequency=entry.get("frequency", "monthly"),
            priority=entry.get("priority", "medium"),
            dashboard=bool(entry.get("dashboard", False)),
            ai=bool(entry.get("ai", False)),
            historical=entry.get("historical", "1y"),
            retention=entry.get("retention", "1y"),
            unit=entry.get("unit", ""),
            description=entry.get("description", ""),
            provider_primary=entry.get("provider_primary", ""),
            provider_secondary=entry.get("provider_secondary"),
            provider_fallback=entry.get("provider_fallback"),
        )
```

- [ ] **Step 4: Ejecutar tests**

```
python -m pytest tests/test_catalog.py -v
```
Expected: `9 passed`

- [ ] **Step 5: Verificar que `market:health` sigue funcionando**

```
python run_poc.py market:health
```
Expected: tabla igual que antes, sin errores.

- [ ] **Step 6: Commit**

```bash
git add catalog/__init__.py tests/test_catalog.py
git commit -m "feat: add CatalogLoader with validation and filtering"
```

---

## Task 4: Actualizar BaseAdapter con soporte de indicator_id

**Files:**
- Modify: `adapters/base.py`
- Create: `tests/test_base_adapter_indicator.py`

**Interfaces:**
- Consumes: nada nuevo
- Produce:
  - `BaseAdapter.supported_indicators: dict[str, dict]` — campo de clase, por defecto `{}`
  - `BaseAdapter.supports(indicator_id: str) -> bool`
  - `BaseAdapter.fetch(indicator_id: str | None = None) -> AdapterResult` — firma actualizada

- [ ] **Step 1: Escribir tests**

```python
# tests/test_base_adapter_indicator.py
from adapters.base import BaseAdapter
from models.base import AdapterResult, ProviderMetadata
from datetime import datetime


class _LegacyAdapter(BaseAdapter):
    name = "Legacy"
    category = "macro"
    region = "Global"

    def fetch(self, indicator_id=None):
        metadata = self._make_metadata()
        return AdapterResult(
            provider=self.name, success=True, records=[],
            error=None, latency_ms=10.0, raw_sample=None, metadata=metadata,
        )


class _MigratedAdapter(BaseAdapter):
    name = "Migrated"
    category = "macro"
    region = "Global"
    supported_indicators = {
        "euribor_3m": {"series": "BE001"},
        "euribor_12m": {"series": "BE002"},
    }

    def fetch(self, indicator_id=None):
        metadata = self._make_metadata()
        return AdapterResult(
            provider=self.name, success=True, records=[],
            error=None, latency_ms=10.0, raw_sample=None, metadata=metadata,
        )


def test_legacy_adapter_has_no_supported_indicators():
    adapter = _LegacyAdapter()
    assert adapter.supported_indicators == {}


def test_legacy_adapter_supports_nothing():
    adapter = _LegacyAdapter()
    assert adapter.supports("euribor_3m") is False


def test_migrated_adapter_supports_declared_indicators():
    adapter = _MigratedAdapter()
    assert adapter.supports("euribor_3m") is True
    assert adapter.supports("euribor_12m") is True


def test_migrated_adapter_does_not_support_undeclared():
    adapter = _MigratedAdapter()
    assert adapter.supports("pib_spain") is False


def test_legacy_fetch_accepts_none():
    adapter = _LegacyAdapter()
    result = adapter.fetch(indicator_id=None)
    assert result.success is True


def test_legacy_fetch_accepts_indicator_id_without_crash():
    adapter = _LegacyAdapter()
    result = adapter.fetch(indicator_id="euribor_3m")
    assert result is not None
```

- [ ] **Step 2: Ejecutar tests para verificar fallo**

```
python -m pytest tests/test_base_adapter_indicator.py -v
```
Expected: los tests de `supports()` fallarán con `AttributeError: '_LegacyAdapter' object has no attribute 'supports'`

- [ ] **Step 3: Modificar `adapters/base.py`**

Añadir después de `priority: str = "fallback"` la línea:
```python
    supported_indicators: dict[str, dict] = {}
```

Añadir después del método `is_available()`:
```python
    def supports(self, indicator_id: str) -> bool:
        return indicator_id in self.supported_indicators
```

Cambiar la firma de `fetch` en el ABC de:
```python
    @abstractmethod
    def fetch(self) -> AdapterResult:
        ...
```
a:
```python
    @abstractmethod
    def fetch(self, indicator_id: str | None = None) -> AdapterResult:
        ...
```

El archivo completo resultante:

```python
from abc import ABC, abstractmethod
from datetime import datetime
import time

from models.base import AdapterResult, ProviderHealth, ProviderMetadata, ProviderStatus
from config.settings import get_api_key


class BaseAdapter(ABC):
    name: str
    category: str
    region: str
    requires_api_key: bool = False
    api_key_names: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    priority: str = "fallback"
    supported_indicators: dict[str, dict] = {}

    @abstractmethod
    def fetch(self, indicator_id: str | None = None) -> AdapterResult:
        ...

    def supports(self, indicator_id: str) -> bool:
        return indicator_id in self.supported_indicators

    def is_available(self) -> bool:
        if self.requires_api_key:
            key_names = self.api_key_names or (self.name,)
            return any(get_api_key(name) is not None for name in key_names)
        return True

    def _make_metadata(self, **kwargs) -> ProviderMetadata:
        return ProviderMetadata(
            name=self.name,
            id=kwargs.get("id", self.name.lower().replace(" ", "_")),
            category=self.category,
            region=self.region,
            method=kwargs.get("method", "api"),
            base_url=kwargs.get("base_url", ""),
            requires_api_key=self.requires_api_key,
            declared_update_frequency=kwargs.get("declared_update_frequency", "unknown"),
            declared_historical_depth_years=kwargs.get("declared_historical_depth_years", 0),
            license=kwargs.get("license", "unknown"),
            notes=kwargs.get("notes", ""),
            capabilities=kwargs.get("capabilities", self.capabilities),
            priority=kwargs.get("priority", self.priority),
        )

    def health_check(self, timeout: int = 10) -> ProviderHealth:
        t0 = time.perf_counter()
        try:
            if not self.is_available():
                return ProviderHealth(
                    provider=self.name,
                    status=ProviderStatus.OFFLINE,
                    checked_at=datetime.utcnow(),
                    latency_ms=(time.perf_counter() - t0) * 1000,
                    error="Provider unavailable or required API key missing",
                )
            result = self.fetch()
            status = ProviderStatus.ONLINE if result.success else ProviderStatus.DEGRADED
            return ProviderHealth(
                provider=self.name,
                status=status,
                checked_at=datetime.utcnow(),
                latency_ms=result.latency_ms,
                error=result.error,
            )
        except Exception as exc:
            return ProviderHealth(
                provider=self.name,
                status=ProviderStatus.OFFLINE,
                checked_at=datetime.utcnow(),
                latency_ms=(time.perf_counter() - t0) * 1000,
                error=str(exc),
            )
```

- [ ] **Step 4: Ejecutar tests**

```
python -m pytest tests/test_base_adapter_indicator.py -v
```
Expected: `6 passed`

- [ ] **Step 5: Verificar regresión en tests existentes**

```
python -m pytest tests/ -v
```
Expected: todos los tests anteriores siguen pasando.

- [ ] **Step 6: Verificar `market:health`**

```
python run_poc.py market:health
```
Expected: tabla igual que antes.

- [ ] **Step 7: Commit**

```bash
git add adapters/base.py tests/test_base_adapter_indicator.py
git commit -m "feat: add supported_indicators and fetch(indicator_id) to BaseAdapter"
```

---

## Task 5: BDE adapter con SDMX

**Files:**
- Modify: `adapters/spain/bde.py`
- Create: `tests/test_bde_sdmx.py`

**Interfaces:**
- Consumes: `BaseAdapter.supported_indicators`, `BaseAdapter.fetch(indicator_id)`
- Produce: `BDEAdapter.supported_indicators` con `euribor_3m`, `euribor_12m`, `spain_10y`; `BDEAdapter.fetch(indicator_id)` que llama a SDMX cuando el indicator está soportado y al CSV legacy cuando no.

**Nota sobre el SDMX de BDE:** La API SDMX de BIEST (BDE) usa la siguiente URL base:
`https://www.bde.es/webbde/es/estadis/biest/Brindice.jsp`
Para datos via SDMX REST, la URL es:
`https://sdmx.bde.es/service/data/{flowRef}/{key}`
Verificar los codes exactos en https://www.bde.es/webbde/es/estadis/biest/ durante la implementación.

- [ ] **Step 1: Investigar el endpoint SDMX de BDE**

Ejecutar para verificar que el endpoint SDMX responde:
```bash
python -c "
import requests
# Test SDMX endpoint BDE
url = 'https://sdmx.bde.es/service/data/TIPO/M.IT.MIR.14.A.2500.EUR.2250.N?format=jsondata&lastNObservations=3'
r = requests.get(url, timeout=15, headers={'Accept': 'application/json'})
print('Status:', r.status_code)
print('Content-Type:', r.headers.get('content-type'))
print('Preview:', r.text[:500])
"
```

Si el endpoint devuelve 200 con JSON, usar ese formato. Si no, probar:
```bash
python -c "
import requests
url = 'https://www.bde.es/webbde/es/estadis/infoest/Series/si_1_1.csv'
r = requests.get(url, timeout=15)
print('CSV status:', r.status_code)
print('Preview:', r.text[:300])
"
```

Anotar qué URLs funcionan antes de proceder.

- [ ] **Step 2: Escribir tests con mock**

```python
# tests/test_bde_sdmx.py
from unittest.mock import patch, Mock
from adapters.spain.bde import BDEAdapter


def _mock_sdmx_response(indicator_id: str):
    """Simula una respuesta SDMX exitosa del BDE."""
    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = Mock()
    # Simular respuesta JSON SDMX mínima
    mock_resp.json.return_value = {
        "dataSets": [{
            "series": {
                "0:0:0": {
                    "observations": {
                        "0": [3.5, 0, None],
                        "1": [3.4, 0, None],
                    }
                }
            }
        }],
        "structure": {
            "dimensions": {
                "observation": [{"values": [{"id": "2024-01"}, {"id": "2024-02"}]}]
            }
        }
    }
    return mock_resp


def test_bde_supports_euribor_3m():
    adapter = BDEAdapter()
    assert adapter.supports("euribor_3m") is True


def test_bde_supports_euribor_12m():
    adapter = BDEAdapter()
    assert adapter.supports("euribor_12m") is True


def test_bde_supports_spain_10y():
    adapter = BDEAdapter()
    assert adapter.supports("spain_10y") is True


def test_bde_does_not_support_unknown():
    adapter = BDEAdapter()
    assert adapter.supports("cpi_usa") is False


def test_bde_fetch_without_indicator_uses_legacy():
    adapter = BDEAdapter()
    with patch("adapters.spain.bde.requests.head") as mock_head, \
         patch("adapters.spain.bde.requests.get") as mock_get:
        mock_head.return_value = Mock(status_code=200)
        mock_get.return_value = Mock(
            status_code=200,
            text="date;value\n2024-01;3.5\n",
            raise_for_status=Mock(),
        )
        result = adapter.fetch(indicator_id=None)
    assert result is not None
    assert result.provider == "Banco de España"


def test_bde_fetch_with_unsupported_indicator_uses_legacy():
    adapter = BDEAdapter()
    with patch("adapters.spain.bde.requests.head") as mock_head, \
         patch("adapters.spain.bde.requests.get") as mock_get:
        mock_head.return_value = Mock(status_code=200)
        mock_get.return_value = Mock(
            status_code=200,
            text="date;value\n2024-01;3.5\n",
            raise_for_status=Mock(),
        )
        result = adapter.fetch(indicator_id="cpi_usa")
    assert result is not None
```

- [ ] **Step 3: Ejecutar tests para verificar fallo**

```
python -m pytest tests/test_bde_sdmx.py -v
```
Expected: `test_bde_supports_euribor_3m` fallará porque `BDEAdapter` no tiene `supported_indicators`.

- [ ] **Step 4: Reescribir `adapters/spain/bde.py`**

```python
"""Banco de España adapter — SDMX para series clave, CSV legacy como fallback."""
import time
import requests
from datetime import datetime, timezone

from adapters.base import BaseAdapter
from models.base import AdapterResult, ProviderMetadata
from models.macro import MacroIndicator

_SDMX_BASE = "https://sdmx.bde.es/service/data"
_SDMX_HEADERS = {
    "Accept": "application/vnd.sdmx.data+json;version=1.0",
    "User-Agent": "MarketDataPOC/0.1 contact@example.com",
}
_PRIMARY_URL = "https://www.bde.es/webbde/es/estadis/infoest/Series/si_1_1.csv"
_FALLBACK_URL = (
    "https://www.bde.es/f/webbde/SES/Secciones/Publicaciones/InformesBoletinesRevistas"
    "/BoletinEstadistico/25/T01/Fich/be_1-1.csv"
)

# Códigos SDMX BDE — verificar en https://sdmx.bde.es/service/dataflow
_SDMX_SERIES = {
    "euribor_3m": {
        "flow": "TIPO",
        "key": "M.IT.MIR.14.A.2500.EUR.2250.N",
        "indicator_id": "EURIBOR_3M",
        "name": "Euribor 3 meses",
        "unit": "%",
        "frequency": "monthly",
    },
    "euribor_12m": {
        "flow": "TIPO",
        "key": "M.IT.MIR.14.A.2500.EUR.2253.N",
        "indicator_id": "EURIBOR_12M",
        "name": "Euribor 12 meses",
        "unit": "%",
        "frequency": "monthly",
    },
    "spain_10y": {
        "flow": "BONO",
        "key": "M.ES.GVT.10Y",
        "indicator_id": "SPAIN_10Y",
        "name": "Bono Español 10Y",
        "unit": "%",
        "frequency": "monthly",
    },
}


class BDEAdapter(BaseAdapter):
    name = "Banco de España"
    category = "macro"
    region = "Spain"
    requires_api_key = False
    supported_indicators = {k: v for k, v in _SDMX_SERIES.items()}

    def is_available(self) -> bool:
        try:
            r = requests.head(_PRIMARY_URL, timeout=10)
            return r.status_code < 500
        except Exception:
            return False

    def fetch(self, indicator_id: str | None = None) -> AdapterResult:
        if indicator_id and indicator_id in _SDMX_SERIES:
            return self._fetch_sdmx(indicator_id)
        return self._fetch_legacy()

    def _fetch_sdmx(self, indicator_id: str) -> AdapterResult:
        series = _SDMX_SERIES[indicator_id]
        url = f"{_SDMX_BASE}/{series['flow']}/{series['key']}?lastNObservations=12"
        metadata = self._make_metadata(base_url=url, method="sdmx")
        t0 = time.time()
        try:
            r = requests.get(url, headers=_SDMX_HEADERS, timeout=15)
            latency_ms = (time.time() - t0) * 1000
            r.raise_for_status()
            records = self._parse_sdmx(r.json(), series)
        except Exception as exc:
            latency_ms = (time.time() - t0) * 1000
            return AdapterResult(
                provider=self.name, success=False, records=[],
                error=f"SDMX error: {exc}", latency_ms=latency_ms,
                raw_sample=None, metadata=metadata,
            )
        return AdapterResult(
            provider=self.name,
            success=bool(records),
            records=records,
            error=None if records else "No SDMX observations parsed",
            latency_ms=latency_ms,
            raw_sample=None,
            metadata=metadata,
        )

    def _parse_sdmx(self, data: dict, series: dict) -> list[MacroIndicator]:
        retrieved_at = datetime.now(timezone.utc)
        records: list[MacroIndicator] = []
        try:
            dataset = data["dataSets"][0]
            series_data = dataset["series"]
            dimensions = data["structure"]["dimensions"]["observation"][0]["values"]
            for _series_key, series_obj in series_data.items():
                for obs_key, obs_values in series_obj["observations"].items():
                    idx = int(obs_key)
                    value = obs_values[0]
                    if value is None:
                        continue
                    period = dimensions[idx]["id"] if idx < len(dimensions) else str(idx)
                    records.append(MacroIndicator(
                        provider=self.name,
                        source=f"{_SDMX_BASE}/{series['flow']}/{series['key']}",
                        retrieved_at=retrieved_at,
                        country="Spain",
                        region=self.region,
                        confidence_score=0.95,
                        indicator_id=series["indicator_id"],
                        name=series["name"],
                        value=float(value),
                        unit=series["unit"],
                        period=period,
                        frequency=series["frequency"],
                    ))
        except (KeyError, IndexError, TypeError):
            pass
        return records

    def _fetch_legacy(self) -> AdapterResult:
        metadata = self._make_metadata(base_url=_PRIMARY_URL)
        t0 = time.time()
        try:
            response = self._get_csv(t0)
        except Exception as exc:
            latency_ms = (time.time() - t0) * 1000
            return AdapterResult(
                provider=self.name, success=False, records=[],
                error=str(exc), latency_ms=latency_ms,
                raw_sample=None, metadata=metadata,
            )
        raw_text, latency_ms, used_url = response
        metadata = self._make_metadata(base_url=used_url)
        try:
            records = self._parse_csv(raw_text)
        except Exception as exc:
            return AdapterResult(
                provider=self.name, success=False, records=[],
                error=f"Parse error: {exc}", latency_ms=latency_ms,
                raw_sample=None, metadata=metadata,
            )
        raw_sample = {"raw_preview": raw_text[:500]} if raw_text else None
        return AdapterResult(
            provider=self.name,
            success=bool(records),
            records=records,
            error=None if records else "No BDE data parsed",
            latency_ms=latency_ms,
            raw_sample=raw_sample,
            metadata=metadata,
        )

    def _get_csv(self, t0: float):
        for url in (_PRIMARY_URL, _FALLBACK_URL):
            try:
                r = requests.get(url, timeout=10)
                latency_ms = (time.time() - t0) * 1000
                r.raise_for_status()
                return r.text, latency_ms, url
            except Exception:
                pass
        raise RuntimeError("Both BDE CSV URLs failed")

    def _parse_csv(self, raw_text: str) -> list:
        import csv
        retrieved_at = datetime.now(timezone.utc)
        lines = raw_text.splitlines()
        header = None
        data_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if header is None and (";" in stripped or "," in stripped) and not stripped[0].isdigit():
                header = stripped
                continue
            first_char = stripped[0]
            if first_char.isdigit() or (len(stripped) > 4 and stripped[1:5].isdigit()):
                data_lines.append(stripped)
        delimiter = ";" if (header or "").count(";") >= (header or "").count(",") else ","
        rows = list(csv.reader(data_lines[-5:], delimiter=delimiter))
        if not rows:
            rows = list(csv.reader(data_lines[-3:], delimiter=","))
            delimiter = ","
        headers = list(csv.reader([header], delimiter=delimiter))[0] if header else []
        records: list[MacroIndicator] = []
        for row in rows:
            if len(row) < 2:
                continue
            period = row[0].strip()
            for idx, cell in enumerate(row[1:], start=1):
                try:
                    value = float(cell.strip().replace(",", "."))
                except (ValueError, IndexError):
                    continue
                label = headers[idx] if idx < len(headers) else f"Serie {idx}"
                indicator_id, name, unit = _classify_bde_series(label)
                records.append(MacroIndicator(
                    provider=self.name, source=_PRIMARY_URL,
                    retrieved_at=retrieved_at, country="Spain", region=self.region,
                    confidence_score=0.9 if headers else 0.75,
                    indicator_id=indicator_id, name=name,
                    value=value, unit=unit, period=period, frequency="monthly",
                ))
        return records


def _classify_bde_series(label: str) -> tuple[str, str, str]:
    label_lower = label.lower()
    if "euribor" in label_lower:
        return "ES_EURIBOR", label or "Euribor", "%"
    if "bce" in label_lower or "facilidad" in label_lower or "intervencion" in label_lower:
        return "ECB_RATE", label or "Tipo BCE", "%"
    if "ipc" in label_lower or "inflaci" in label_lower:
        return "ES_INFLATION", label or "Inflacion", "%"
    if "m1" in label_lower or "m2" in label_lower or "m3" in label_lower:
        return "ES_MONEY_SUPPLY", label or "Indicador monetario", ""
    return "BDE_SERIES", label or "Banco de Espana series", ""
```

- [ ] **Step 5: Ejecutar tests BDE**

```
python -m pytest tests/test_bde_sdmx.py -v
```
Expected: `6 passed`

- [ ] **Step 6: Probar BDE contra SDMX real**

```bash
python -c "
from adapters.spain.bde import BDEAdapter
a = BDEAdapter()
result = a.fetch('euribor_3m')
print('Success:', result.success)
print('Records:', len(result.records))
print('Error:', result.error)
if result.records:
    r = result.records[0]
    print('Sample:', r.indicator_id, r.value, r.unit, r.period)
"
```

Si SDMX falla con 404/error: los códigos de series (`flow` y `key`) necesitan ajustarse. Ver Step 1 de esta tarea para investigar los endpoints correctos. El test unitario mock seguirá pasando; solo el test de integración fallará hasta encontrar los códigos correctos.

- [ ] **Step 7: Verificar `market:health`**

```
python run_poc.py market:health
```
Expected: BDE debe aparecer como `online` o al menos con latency, sin regresión en otros providers.

- [ ] **Step 8: Commit**

```bash
git add adapters/spain/bde.py tests/test_bde_sdmx.py
git commit -m "feat: migrate BDE adapter to SDMX with CSV legacy fallback"
```

---

## Task 6: fetch_indicator en ProviderOrchestrator

**Files:**
- Modify: `services/orchestrator.py`
- Create: `tests/test_catalog_orchestrator.py`

**Interfaces:**
- Consumes:
  - `CatalogIndicator` de `models/catalog.py`
  - `CatalogFetchResult` de `models/catalog.py`
  - `BaseAdapter.supports(indicator_id)` de Task 4
  - `BaseAdapter.fetch(indicator_id)` de Task 4
- Produce:
  - `ProviderOrchestrator._get_adapter(provider_id: str) -> BaseAdapter | None`
  - `ProviderOrchestrator.fetch_indicator(indicator: CatalogIndicator) -> CatalogFetchResult`

- [ ] **Step 1: Escribir tests**

```python
# tests/test_catalog_orchestrator.py
from unittest.mock import Mock
from models.catalog import CatalogIndicator, CatalogFetchResult
from models.base import AdapterResult, ProviderMetadata
from services.orchestrator import ProviderOrchestrator


def _make_metadata(name="TestAdapter"):
    return ProviderMetadata(
        name=name, id=name.lower(), category="macro", region="Spain",
        method="api", base_url="", requires_api_key=False,
        declared_update_frequency="monthly", declared_historical_depth_years=5,
        license="open",
    )


def _make_indicator(primary="bde", secondary="ecb", fallback=None):
    return CatalogIndicator(
        id="euribor_3m", name="Euribor 3M", category="macro",
        subcategory="interest_rates", country="ES", region="Spain",
        frequency="daily", priority="critical", dashboard=True, ai=True,
        historical="10y", retention="5y", unit="%", description="",
        provider_primary=primary, provider_secondary=secondary,
        provider_fallback=fallback,
    )


def _make_adapter(name, provider_id, supported, success=True):
    adapter = Mock()
    adapter.name = name
    adapter.is_available.return_value = True
    adapter.supports.side_effect = lambda ind_id: ind_id in supported
    meta = _make_metadata(name)
    adapter.fetch.return_value = AdapterResult(
        provider=name, success=success, records=[], error=None,
        latency_ms=50.0, raw_sample=None, metadata=meta,
    )
    # Mock the provider ID via capabilities attr (used by _get_adapter)
    adapter._provider_id = provider_id
    return adapter


def _make_orchestrator(adapters):
    orch = ProviderOrchestrator(adapters)
    # Patch _get_adapter to look up by _provider_id
    def _get_adapter(pid):
        return next((a for a in adapters if a._provider_id == pid), None)
    orch._get_adapter = _get_adapter
    return orch


def test_fetch_indicator_uses_primary():
    bde = _make_adapter("BDE", "bde", {"euribor_3m"})
    ecb = _make_adapter("ECB", "ecb", {"euribor_3m"})
    orch = _make_orchestrator([bde, ecb])
    indicator = _make_indicator()
    result = orch.fetch_indicator(indicator)
    assert isinstance(result, CatalogFetchResult)
    assert result.provider_used == "bde"
    assert result.fallback_used is False
    assert result.catalog_id == "euribor_3m"


def test_fetch_indicator_falls_back_to_secondary_when_primary_fails():
    bde = _make_adapter("BDE", "bde", {"euribor_3m"}, success=False)
    ecb = _make_adapter("ECB", "ecb", {"euribor_3m"}, success=True)
    orch = _make_orchestrator([bde, ecb])
    indicator = _make_indicator()
    result = orch.fetch_indicator(indicator)
    assert result.provider_used == "ecb"
    assert result.fallback_used is True


def test_fetch_indicator_skips_unsupported_providers():
    bde = _make_adapter("BDE", "bde", set())  # no soporta euribor_3m
    ecb = _make_adapter("ECB", "ecb", {"euribor_3m"})
    orch = _make_orchestrator([bde, ecb])
    indicator = _make_indicator()
    result = orch.fetch_indicator(indicator)
    assert result.provider_used == "ecb"
    assert result.fallback_used is True


def test_fetch_indicator_returns_failed_result_when_no_provider_works():
    bde = _make_adapter("BDE", "bde", set())
    orch = _make_orchestrator([bde])
    indicator = _make_indicator(primary="bde", secondary=None, fallback=None)
    result = orch.fetch_indicator(indicator)
    assert isinstance(result, CatalogFetchResult)
    assert result.adapter_result.success is False
```

- [ ] **Step 2: Ejecutar tests para verificar fallo**

```
python -m pytest tests/test_catalog_orchestrator.py -v
```
Expected: `AttributeError: 'ProviderOrchestrator' object has no attribute 'fetch_indicator'`

- [ ] **Step 3: Modificar `services/orchestrator.py`**

Añadir al principio del archivo los imports:
```python
from models.catalog import CatalogIndicator, CatalogFetchResult
```

Añadir dentro de la clase `ProviderOrchestrator` el método `_get_adapter` y `fetch_indicator`:

```python
    def _get_adapter(self, provider_id: str) -> BaseAdapter | None:
        return next(
            (a for a in self.adapters if getattr(a, "_provider_id", None) == provider_id
             or a.name.lower().replace(" ", "_") == provider_id
             or getattr(a, "provider_id", None) == provider_id),
            None,
        )

    def fetch_indicator(self, indicator: CatalogIndicator) -> CatalogFetchResult:
        chain = [
            indicator.provider_primary,
            indicator.provider_secondary,
            indicator.provider_fallback,
        ]
        for provider_id in [p for p in chain if p]:
            adapter = self._get_adapter(provider_id)
            if adapter is None or not adapter.supports(indicator.id):
                continue
            result = adapter.fetch(indicator.id)
            if result.success:
                return CatalogFetchResult(
                    indicator=indicator,
                    adapter_result=result,
                    provider_used=provider_id,
                    fallback_used=(provider_id != indicator.provider_primary),
                    catalog_id=indicator.id,
                )
        metadata = ProviderMetadata(
            name="Catalog Orchestrator", id="catalog_orchestrator",
            category="orchestration", region="Global", method="internal",
            base_url="", requires_api_key=False,
            declared_update_frequency="unknown",
            declared_historical_depth_years=0, license="internal",
        )
        return CatalogFetchResult(
            indicator=indicator,
            adapter_result=AdapterResult(
                provider="Catalog Orchestrator", success=False, records=[],
                error=f"No migrated provider supports '{indicator.id}'",
                latency_ms=0.0, raw_sample=None, metadata=metadata,
            ),
            provider_used="none",
            fallback_used=False,
            catalog_id=indicator.id,
        )
```

- [ ] **Step 4: Ejecutar tests**

```
python -m pytest tests/test_catalog_orchestrator.py -v
```
Expected: `4 passed`

- [ ] **Step 5: Ejecutar todos los tests**

```
python -m pytest tests/ -v
```
Expected: todos los tests existentes siguen pasando.

- [ ] **Step 6: Commit**

```bash
git add services/orchestrator.py tests/test_catalog_orchestrator.py
git commit -m "feat: add fetch_indicator to ProviderOrchestrator"
```

---

## Task 7: CLI commands del catálogo

**Files:**
- Modify: `run_poc.py`

**Interfaces:**
- Consumes: `CatalogLoader` de `catalog/__init__.py`, `ProviderOrchestrator.fetch_indicator()` de Task 6
- Produce: comandos `market:catalog`, `market:catalog:validate`, `market:catalog:list`, `market:catalog:coverage`, `market:update`

- [ ] **Step 1: Añadir imports y comando al parser en `run_poc.py`**

Al inicio del archivo, después de los imports existentes, añadir:
```python
from catalog import CatalogLoader
from models.catalog import CatalogIndicator, CatalogFetchResult
```

En la lista `choices` del argumento `command` (línea ~341), añadir los nuevos comandos:
```python
        choices=[
            "market:poc",
            "market:health",
            "market:coverage",
            "market:providers",
            "market:compare",
            "market:report",
            "market:cache:clear",
            "market:test",
            "market:currency",
            "market:bonds",
            "market:gaps",
            "market:stabilize",
            "market:catalog",
            "market:catalog:validate",
            "market:catalog:list",
            "market:catalog:coverage",
            "market:update",
        ],
```

Añadir argumento `--priority` al parser:
```python
    parser.add_argument(
        "--priority",
        default=None,
        choices=["critical", "high", "medium", "low"],
        help="Filter catalog by priority (used with market:catalog:list and market:update)",
    )
    parser.add_argument(
        "--category",
        default=None,
        help="Filter catalog by category (used with market:catalog:list)",
    )
```

- [ ] **Step 2: Añadir funciones helper para los comandos**

Añadir estas funciones al archivo `run_poc.py` antes de `def main()`:

```python
def cmd_catalog_show(loader: CatalogLoader) -> None:
    table = Table(title="Market Data Catalog", show_lines=True)
    table.add_column("ID", style="bold")
    table.add_column("Name")
    table.add_column("Priority")
    table.add_column("Freq")
    table.add_column("Dash")
    table.add_column("AI")
    table.add_column("Primary")
    table.add_column("Secondary")
    table.add_column("Fallback")
    for ind in loader.load_all():
        priority_color = {
            "critical": "red", "high": "yellow",
            "medium": "cyan", "low": "dim",
        }.get(ind.priority, "white")
        table.add_row(
            ind.id, ind.name,
            f"[{priority_color}]{ind.priority}[/{priority_color}]",
            ind.frequency,
            "✓" if ind.dashboard else "",
            "✓" if ind.ai else "",
            ind.provider_primary,
            ind.provider_secondary or "",
            ind.provider_fallback or "",
        )
    console.print(table)
    indicators = loader.load_all()
    console.print(f"\nTotal: {len(indicators)} indicators | "
                  f"Critical: {sum(1 for i in indicators if i.priority=='critical')} | "
                  f"High: {sum(1 for i in indicators if i.priority=='high')} | "
                  f"Dashboard: {sum(1 for i in indicators if i.dashboard)} | "
                  f"AI: {sum(1 for i in indicators if i.ai)}")


def cmd_catalog_validate(loader: CatalogLoader) -> bool:
    errors = loader.validate()
    if not errors:
        console.print("[green]✓ Catalog valid — no errors found[/green]")
        console.print(f"  {len(loader.load_all())} indicators loaded from catalog/")
        return True
    console.print(f"[red]✗ Catalog has {len(errors)} error(s):[/red]")
    for err in errors:
        console.print(f"  [red]• {err}[/red]")
    return False


def cmd_catalog_list(loader: CatalogLoader, priority: str | None, category: str | None) -> None:
    indicators = loader.load_all()
    if priority:
        indicators = [i for i in indicators if i.priority == priority]
    if category:
        indicators = [i for i in indicators if i.category == category]
    table = Table(title=f"Catalog — priority={priority or 'all'} category={category or 'all'}", show_lines=True)
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Priority")
    table.add_column("Category")
    table.add_column("Freq")
    table.add_column("Provider")
    for ind in indicators:
        table.add_row(ind.id, ind.name, ind.priority, ind.category, ind.frequency, ind.provider_primary)
    console.print(table)
    console.print(f"Total: {len(indicators)}")


def cmd_catalog_coverage(loader: CatalogLoader, adapters: list) -> None:
    from services.orchestrator import ProviderOrchestrator
    orch = ProviderOrchestrator(adapters)
    indicators = loader.load_all()
    table = Table(title="Catalog Coverage", show_lines=True)
    table.add_column("ID")
    table.add_column("Priority")
    table.add_column("Primary")
    table.add_column("Migrated?")
    table.add_column("Secondary")
    table.add_column("Fallback")
    migrated = 0
    for ind in indicators:
        adapter = orch._get_adapter(ind.provider_primary)
        is_migrated = adapter is not None and adapter.supports(ind.id)
        if is_migrated:
            migrated += 1
        table.add_row(
            ind.id, ind.priority, ind.provider_primary,
            "[green]✓[/green]" if is_migrated else "[red]✗[/red]",
            ind.provider_secondary or "",
            ind.provider_fallback or "",
        )
    console.print(table)
    console.print(f"\nMigrated: {migrated}/{len(indicators)} indicators have a migrated primary provider")


def cmd_market_update(loader: CatalogLoader, adapters: list, timestamp: str, output_formats: set) -> None:
    from services.orchestrator import ProviderOrchestrator
    from exporters.csv_exporter import export_catalog_results
    orch = ProviderOrchestrator(adapters)
    indicators = loader.get_by_priority("critical", "high")
    console.print(f"Fetching {len(indicators)} indicators (critical + high priority)...")
    results: list[CatalogFetchResult] = []
    for ind in indicators:
        console.print(f"  [{ind.priority}] {ind.id} ...", end="")
        cfr = orch.fetch_indicator(ind)
        results.append(cfr)
        status = "[green]OK[/green]" if cfr.adapter_result.success else "[red]FAIL[/red]"
        provider = cfr.provider_used
        console.print(f" {status} ({provider})")
    successful = sum(1 for r in results if r.adapter_result.success)
    console.print(f"\nDone: {successful}/{len(results)} successful")
    if "csv" in output_formats:
        path = export_catalog_results(results, timestamp)
        console.print(f"[green]CSV:[/green] {path}")
    _print_catalog_report(results)


def _print_catalog_report(results: list) -> None:
    total = len(results)
    ok = sum(1 for r in results if r.adapter_result.success)
    fallback_used = sum(1 for r in results if r.fallback_used)
    table = Table(title="Market Catalog Report", show_lines=True)
    table.add_column("Indicator")
    table.add_column("Status")
    table.add_column("Provider used")
    table.add_column("Fallback?")
    table.add_column("Records")
    for r in results:
        status_str = "[green]OK[/green]" if r.adapter_result.success else "[red]FAIL[/red]"
        table.add_row(
            r.catalog_id,
            status_str,
            r.provider_used,
            "yes" if r.fallback_used else "no",
            str(len(r.adapter_result.records)),
        )
    console.print(table)
    console.print(f"Total: {ok}/{total} OK | Fallbacks used: {fallback_used}")
```

- [ ] **Step 3: Añadir los handlers de comandos en `main()`**

En la función `main()`, después del bloque `if args.command == "market:cache:clear":`, añadir:

```python
    # Catalog commands — ejecutar antes de cargar adapters cuando sea posible
    catalog_loader = CatalogLoader()

    if args.command == "market:catalog":
        cmd_catalog_show(catalog_loader)
        return

    if args.command == "market:catalog:validate":
        valid = cmd_catalog_validate(catalog_loader)
        sys.exit(0 if valid else 1)

    if args.command == "market:catalog:list":
        cmd_catalog_list(catalog_loader, args.priority, args.category)
        return

    if args.command == "market:catalog:coverage":
        cmd_catalog_coverage(catalog_loader, available)
        return

    if args.command == "market:update":
        cmd_market_update(catalog_loader, available, timestamp, output_formats)
        return
```

- [ ] **Step 4: Probar los comandos**

```bash
python run_poc.py market:catalog:validate
```
Expected: `✓ Catalog valid — no errors found` y `52 indicators loaded`

```bash
python run_poc.py market:catalog
```
Expected: tabla con ~52 filas.

```bash
python run_poc.py market:catalog:list --priority critical
```
Expected: tabla filtrada con solo los indicadores critical.

```bash
python run_poc.py market:catalog:list --category forex
```
Expected: 8 indicadores forex.

- [ ] **Step 5: Verificar que `market:health` sigue funcionando**

```
python run_poc.py market:health
```
Expected: tabla igual que antes.

- [ ] **Step 6: Commit**

```bash
git add run_poc.py
git commit -m "feat: add market:catalog, market:catalog:validate, market:catalog:list, market:catalog:coverage CLI commands"
```

---

## Task 8: export_catalog_results en CSV exporter y market:update

**Files:**
- Modify: `exporters/csv_exporter.py`
- Create: `tests/test_catalog_csv.py`

**Interfaces:**
- Consumes: `CatalogFetchResult` de `models/catalog.py`
- Produce: `export_catalog_results(results: list[CatalogFetchResult], timestamp: str | None) -> Path`

- [ ] **Step 1: Escribir tests**

```python
# tests/test_catalog_csv.py
import dataclasses
from pathlib import Path
from models.catalog import CatalogIndicator, CatalogFetchResult
from models.base import AdapterResult, ProviderMetadata
from models.macro import MacroIndicator
from datetime import datetime, timezone
from exporters.csv_exporter import export_catalog_results


def _make_metadata():
    return ProviderMetadata(
        name="BDE", id="bde", category="macro", region="Spain",
        method="sdmx", base_url="", requires_api_key=False,
        declared_update_frequency="monthly", declared_historical_depth_years=10,
        license="open",
    )


def _make_cfr(indicator_id="euribor_3m", success=True, n_records=2):
    ind = CatalogIndicator(
        id=indicator_id, name="Test", category="macro", subcategory="rates",
        country="ES", region="Spain", frequency="daily", priority="critical",
        dashboard=True, ai=True, historical="10y", retention="5y",
        unit="%", description="", provider_primary="bde",
    )
    now = datetime.now(timezone.utc)
    records = [
        MacroIndicator(
            provider="BDE", source="url", retrieved_at=now,
            country="ES", region="Spain", confidence_score=0.95,
            indicator_id=indicator_id, name="Test", value=3.5 + i,
            unit="%", period=f"2024-0{i+1}", frequency="monthly",
        )
        for i in range(n_records)
    ]
    return CatalogFetchResult(
        indicator=ind,
        adapter_result=AdapterResult(
            provider="BDE", success=success, records=records,
            error=None, latency_ms=50.0, raw_sample=None, metadata=_make_metadata(),
        ),
        provider_used="bde",
        fallback_used=False,
        catalog_id=indicator_id,
    )


def test_export_catalog_results_creates_file(tmp_path):
    results = [_make_cfr("euribor_3m"), _make_cfr("eur_usd", n_records=1)]
    path = export_catalog_results(results, timestamp="20260626T000000", output_dir=tmp_path)
    assert path.exists()
    assert path.suffix == ".csv"


def test_export_catalog_results_includes_catalog_fields(tmp_path):
    import pandas as pd
    results = [_make_cfr("euribor_3m")]
    path = export_catalog_results(results, timestamp="20260626T000001", output_dir=tmp_path)
    df = pd.read_csv(path)
    assert "catalog_id" in df.columns
    assert "priority" in df.columns
    assert "dashboard" in df.columns
    assert "ai" in df.columns
    assert "provider_used" in df.columns
    assert "fallback_used" in df.columns
    assert df["catalog_id"].iloc[0] == "euribor_3m"
    assert df["priority"].iloc[0] == "critical"
    assert df["dashboard"].iloc[0] == True


def test_export_catalog_results_row_count(tmp_path):
    import pandas as pd
    results = [_make_cfr("euribor_3m", n_records=2), _make_cfr("eur_usd", n_records=1)]
    path = export_catalog_results(results, timestamp="20260626T000002", output_dir=tmp_path)
    df = pd.read_csv(path)
    assert len(df) == 3  # 2 + 1 records
```

- [ ] **Step 2: Ejecutar tests para verificar fallo**

```
python -m pytest tests/test_catalog_csv.py -v
```
Expected: `ImportError: cannot import name 'export_catalog_results' from 'exporters.csv_exporter'`

- [ ] **Step 3: Modificar `exporters/csv_exporter.py`**

```python
import dataclasses
from datetime import datetime
from pathlib import Path
from typing import List

import pandas as pd

from models.base import AdapterResult, ProviderRecord

_OUTPUT_DIR = Path(__file__).parent.parent / "output" / "csv"


def export_records(results: List[AdapterResult], timestamp: str | None = None) -> Path:
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = timestamp or datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    path = _OUTPUT_DIR / f"{ts}_all_records.csv"
    rows = []
    for result in results:
        for record in result.records:
            if dataclasses.is_dataclass(record) and not isinstance(record, type):
                rows.append(dataclasses.asdict(record))
            elif isinstance(record, dict):
                rows.append(record)
    df = pd.DataFrame(rows) if rows else pd.DataFrame()
    df.to_csv(path, index=False, encoding="utf-8")
    return path


def export_catalog_results(
    results: list,
    timestamp: str | None = None,
    output_dir: Path | None = None,
) -> Path:
    out_dir = output_dir or _OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = timestamp or datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    path = out_dir / f"{ts}_catalog_records.csv"
    rows = []
    for cfr in results:
        catalog_meta = {
            "catalog_id": cfr.catalog_id,
            "priority": cfr.indicator.priority,
            "dashboard": cfr.indicator.dashboard,
            "ai": cfr.indicator.ai,
            "provider_used": cfr.provider_used,
            "fallback_used": cfr.fallback_used,
        }
        for record in cfr.adapter_result.records:
            if dataclasses.is_dataclass(record) and not isinstance(record, type):
                row = dataclasses.asdict(record)
                row.update(catalog_meta)
                rows.append(row)
            elif isinstance(record, dict):
                row = dict(record)
                row.update(catalog_meta)
                rows.append(row)
    df = pd.DataFrame(rows) if rows else pd.DataFrame()
    df.to_csv(path, index=False, encoding="utf-8")
    return path
```

- [ ] **Step 4: Ejecutar tests**

```
python -m pytest tests/test_catalog_csv.py -v
```
Expected: `3 passed`

- [ ] **Step 5: Ejecutar `market:update` completo**

```
python run_poc.py market:update
```
Expected: fetch de indicadores critical+high, CSV en `output/csv/`, tabla de reporte. La mayoría fallará con "No migrated provider supports..." porque solo BDE está migrado — eso es correcto en esta fase.

- [ ] **Step 6: Verificar que el CSV nuevo tiene ≤100 registros**

```bash
python -c "
import pandas as pd, pathlib, glob
files = sorted(glob.glob('output/csv/*_catalog_records.csv'))
if files:
    df = pd.read_csv(files[-1])
    print(f'Catalog CSV: {len(df)} records, columns: {list(df.columns)}')
"
```
Expected: el número de registros es pequeño (proporcional a cuántos adapters están migrados × observaciones por indicador).

- [ ] **Step 7: Ejecutar todos los tests**

```
python -m pytest tests/ -v
```
Expected: todos pasan.

- [ ] **Step 8: Commit**

```bash
git add exporters/csv_exporter.py tests/test_catalog_csv.py
git commit -m "feat: add export_catalog_results with catalog metadata fields"
```

---

## Task 9: Verificación final de criterios de éxito

- [ ] **Step 1: `market:catalog:validate` pasa sin errores**

```
python run_poc.py market:catalog:validate
```
Expected: `✓ Catalog valid — no errors found` con ≥52 indicators.

- [ ] **Step 2: `market:catalog:coverage` muestra ≥52 indicadores**

```
python run_poc.py market:catalog:coverage
```
Expected: tabla con ≥52 filas. BDE debe aparecer como migrado para `euribor_3m`, `euribor_12m`, `spain_10y`.

- [ ] **Step 3: `market:health` sin regresiones**

```
python run_poc.py market:health
```
Expected: mismos resultados que antes de esta fase. BDE debe aparecer `online` o `degraded` (nunca peor que antes).

- [ ] **Step 4: `market:update` produce CSV reducido**

```
python run_poc.py market:update
```
Expected: CSV catalog con ≤100 registros (vs 11k del CSV legacy). Tabla de reporte visible.

- [ ] **Step 5: Ejecutar suite de tests completa**

```
python -m pytest tests/ -v
```
Expected: todos los tests pasan.

- [ ] **Step 6: Commit de cierre de fase**

```bash
git add -A
git commit -m "feat: Phase 5.4.5 complete — Market Data Catalog with catalog-driven fetch"
```

---

## Self-Review

**Cobertura del spec:**
- ✓ `catalog/` con 9 YAMLs por categoría (Task 2)
- ✓ Schema YAML con todos los campos obligatorios y opcionales (Task 2)
- ✓ 52+ indicadores en todas las categorías del spec (Task 2)
- ✓ `CatalogLoader` con todos los métodos del spec (Task 3)
- ✓ `BaseAdapter.supported_indicators` y `fetch(indicator_id)` (Task 4)
- ✓ BDE migrado a SDMX con legacy fallback (Task 5)
- ✓ `ProviderOrchestrator.fetch_indicator()` (Task 6)
- ✓ 5 CLI commands (Task 7)
- ✓ `export_catalog_results` con campos catalog_id, priority, dashboard, ai, provider_used, fallback_used (Task 8)
- ✓ Market Catalog Report en `market:update` (Task 7 `_print_catalog_report`)
- ✓ 34 adapters no modificados (solo BDE y BaseAdapter tocados)
- ✓ Criterios de éxito verificados en Task 9

**Consistencia de tipos:**
- `CatalogLoader` definido en Task 3, usado en Tasks 7 y 8 ✓
- `CatalogFetchResult` definido en Task 1, producido en Task 6, consumido en Tasks 7 y 8 ✓
- `export_catalog_results(results: list[CatalogFetchResult], timestamp, output_dir)` definido en Task 8, llamado en Task 7 `cmd_market_update` ✓
- `ProviderOrchestrator.fetch_indicator(indicator: CatalogIndicator) -> CatalogFetchResult` definido en Task 6, llamado en Task 7 ✓

**Sin placeholders:** Todos los pasos tienen código completo o comandos exactos.
