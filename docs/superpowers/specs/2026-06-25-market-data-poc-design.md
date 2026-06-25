# Design: Market Data Ingestion POC — Fase 5.4

**Date:** 2026-06-25
**Phase:** 5.4 — Market Data Ingestion POC
**Approach chosen:** Opción A — Explorador secuencial con ThreadPoolExecutor y informe final

---

## Objetivo

Construir un módulo Python completamente aislado (`market-data-poc/`) que descubra, pruebe y evalúe automáticamente todos los proveedores de datos financieros y macroeconómicos gratuitos listados en la spec. El resultado es un informe Markdown + JSON/CSV que permita diseñar el Market Data Hub definitivo.

No toca base de datos, dashboard, IA ni backend existente.

---

## Ubicación

```
AI-Financial-OS/
└── market-data-poc/        ← paquete Python autónomo
    ├── pyproject.toml      # deps propias, sin heredar del backend
    └── ...
```

---

## Estructura de directorios

```
market-data-poc/
├── pyproject.toml
├── README.md
├── run_poc.py                      # entry point CLI
│
├── config/
│   ├── providers.yaml              # catálogo declarativo de proveedores
│   └── settings.py                 # carga .env (API keys opcionales)
│
├── models/
│   ├── base.py                     # ProviderRecord, AdapterResult, ProviderMetadata
│   ├── market.py                   # MarketQuote, HistoricalPrice
│   ├── macro.py                    # MacroIndicator, EconomicEvent
│   ├── company.py                  # CompanyProfile, CompanyMetric, Dividend
│   ├── news.py                     # NewsItem
│   └── evaluation.py               # ProviderEvaluation, CoverageReport
│
├── adapters/
│   ├── base.py                     # BaseAdapter ABC
│   ├── spain/
│   │   ├── bde.py                  # Banco de España — Euribor, tipos, estadísticas
│   │   ├── ine.py                  # INE — IPC, PIB, paro, demografía
│   │   ├── cnmv.py                 # CNMV — fondos, empresas, hechos relevantes
│   │   ├── bme.py                  # BME — mercados españoles, índices
│   │   ├── tesoro.py               # Tesoro Público — bonos, letras
│   │   └── ree.py                  # REE — precio electricidad, consumo
│   ├── europe/
│   │   ├── ecb.py                  # ECB SDW API — tipos, masa monetaria
│   │   ├── eurostat.py             # Eurostat REST — macro Eurozona
│   │   └── oecd.py                 # OECD API — macro OCDE
│   ├── usa/
│   │   ├── fred.py                 # FRED — macro USA + España + Eurozona
│   │   ├── edgar.py                # SEC EDGAR — empresas, fundamentales
│   │   ├── bls.py                  # BLS — empleo USA
│   │   └── treasury.py             # US Treasury — bonos
│   ├── global_/
│   │   ├── world_bank.py           # World Bank API
│   │   ├── imf.py                  # IMF Data API
│   │   ├── coingecko.py            # CoinGecko — cripto
│   │   ├── stooq.py                # Stooq CSV — acciones, índices, forex
│   │   ├── alpha_vantage.py        # Alpha Vantage (key gratuita)
│   │   ├── finnhub.py              # Finnhub (key gratuita)
│   │   ├── fmp.py                  # Financial Modeling Prep (key gratuita)
│   │   └── twelvedata.py           # Twelve Data (key gratuita)
│   └── rss/
│       └── reader.py               # lector RSS genérico + fuentes configuradas
│
├── scrapers/                       # Scrapy — solo fallback
│   ├── settings.py
│   └── spiders/
│       ├── yahoo_finance.py
│       └── investing.py
│
├── services/
│   ├── runner.py                   # orquesta adaptadores con ThreadPoolExecutor
│   └── scorer.py                   # scoring automático 0-100 por dimensión
│
├── validators/
│   └── data_quality.py             # completitud, rango, fresquedad, anomalías
│
├── exporters/
│   ├── json_exporter.py
│   ├── csv_exporter.py
│   └── report_generator.py         # genera informe Markdown
│
└── output/                         # .gitignore — generado en ejecución
    ├── json/
    ├── csv/
    └── reports/
```

---

## Dependencias (pyproject.toml)

```toml
[project]
name = "market-data-poc"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "requests",
    "httpx",
    "pandas",
    "feedparser",       # RSS
    "pyyaml",           # providers.yaml
    "rich",             # terminal output
    "python-dotenv",
    "scrapy",           # scrapers fallback
]
```

---

## Modelos de datos

### Base compartida

```python
@dataclass
class ProviderRecord:
    provider: str
    source: str
    retrieved_at: datetime
    country: str        # "ES", "US", "EA", "GLOBAL"
    region: str         # "Spain", "Eurozone", "USA", "Global"
    confidence_score: float  # 0.0–1.0 — calculado por el adaptador (completitud del registro individual)
```

### Modelos específicos

| Modelo | Campos clave |
|---|---|
| `MarketQuote` | symbol, name, asset_type, price, change_pct, currency, market_status |
| `HistoricalPrice` | symbol, date, open, high, low, close, volume |
| `MacroIndicator` | indicator_id, name, value, unit, period, frequency |
| `CompanyProfile` | symbol, name, sector, industry, market_cap, exchange |
| `CompanyMetric` | symbol, pe_ratio, eps, dividend_yield, beta, revenue |
| `Dividend` | symbol, ex_date, pay_date, amount, currency |
| `EconomicEvent` | event_name, date, forecast, actual, previous, impact |
| `NewsItem` | title, published_at, source_name, url, category, related_asset |

### AdapterResult — contrato del runner

```python
@dataclass
class AdapterResult:
    provider: str
    success: bool
    records: list[ProviderRecord]   # datos normalizados
    error: str | None
    latency_ms: float
    raw_sample: dict | None         # muestra del JSON/CSV crudo
    metadata: ProviderMetadata      # cobertura, límites, licencia
```

### ProviderMetadata — declarada en providers.yaml

```yaml
- name: Banco de España
  category: macro
  region: Spain
  method: api
  base_url: https://www.bde.es/...
  requires_api_key: false
  declared_update_frequency: monthly
  declared_historical_depth_years: 20
  license: open
  notes: "Euribor, tipos, estadísticas financieras"
```

---

## Contrato BaseAdapter

```python
class BaseAdapter(ABC):
    name: str
    category: str           # "macro" | "markets" | "companies" | "news"
    region: str
    requires_api_key: bool

    @abstractmethod
    def fetch(self) -> AdapterResult:
        """Llama al proveedor y devuelve datos normalizados + metadata."""
        ...

    def is_available(self) -> bool:
        """False si requires_api_key y no hay key configurada."""
        ...
```

Cualquier nuevo adaptador que implemente este contrato se integra automáticamente sin tocar runner ni exporters.

---

## Sistema de scoring (ProviderEvaluation)

Cada proveedor recibe puntuación 0-100 en estas dimensiones:

| Dimensión | Peso | Descripción |
|---|---|---|
| `data_quality` | 25% | Completitud y coherencia de los valores recibidos |
| `reliability` | 20% | ¿Respondió? ¿Sin errores HTTP? |
| `coverage_breadth` | 15% | Variedad de asset types soportados |
| `geo_coverage` | 10% | Número de regiones cubiertas |
| `historical_depth` | 10% | Años de histórico disponibles |
| `update_frequency` | 10% | Realtime/daily/weekly/monthly |
| `latency_score` | 5% | Basado en latency_ms medida |
| `integration_complexity` | 3% | Estimado (simple API vs scraping) |
| `legal_risk` | 2% | 0=API oficial, 50=CSV público, 100=scraping |

**Score final** = suma ponderada → **Recomendación automática:**
- ≥ 75: `principal`
- 50–74: `secundario`
- 30–49: `fallback`
- < 30: `descartado`

---

## Flujo de ejecución

```
python run_poc.py [--providers all|spain|europe|usa|global] \
                  [--output json,csv,report] \
                  [--timeout 10] \
                  [--workers 5]
```

1. Cargar `providers.yaml` + `.env` (API keys opcionales)
2. Resolver qué adaptadores ejecutar según `--providers`
3. Filtrar adaptadores no disponibles (`is_available() == False`) → advertencia en terminal
4. `runner.py` lanza adaptadores en `ThreadPoolExecutor(max_workers=5)`
   - Timeout individual de 10s por llamada HTTP
   - Errores capturados sin detener los demás
5. `scorer.py` evalúa cada `AdapterResult` → `ProviderEvaluation`
6. `validators/data_quality.py` marca anomalías en los records
7. Exporters escriben `output/` según `--output`
8. `rich` imprime tabla resumen en terminal

---

## Informe Markdown generado

```markdown
# Market Data POC — Informe <fecha>

## Resumen ejecutivo
Proveedores probados / Exitosos / Fallidos / Tiempo total

## Cobertura por región
España | Europa | USA | Global

## Cobertura por categoría
Macro | Mercados | Empresas | Noticias

## Ranking de proveedores
| # | Proveedor | Score | Calidad | Fiabilidad | Cobertura | Recomendación |

## Mejor proveedor por asset type
Acciones / ETFs / Fondos / Índices / Cripto / Macro / Empresas / Noticias / Calendario

## Limitaciones detectadas
API keys necesarias / Rate limits / Problemas detectados / Licencias restrictivas

## Recomendaciones finales
Principal / Secundario / Fallback / Descartados — con justificación
```

---

## Proveedores en scope

### España (prioridad máxima)
Banco de España, INE, CNMV, BME, Tesoro Público, REE

### Europa
ECB, Eurostat, OECD

### USA
FRED, SEC EDGAR, BLS, US Treasury

### Global
World Bank, IMF, CoinGecko, Stooq, Alpha Vantage, Finnhub, FMP, TwelveData

### RSS
Expansión, Cinco Días, El Economista, Reuters Markets, CNBC, ECB News, Federal Reserve News

### Scraping (fallback)
Yahoo Finance, Investing.com — via Scrapy

---

## Restricciones

- No modifica base de datos, dashboard, IA ni backend existente
- No importa código de `backend/app/`
- Sin servidor HTTP propio — ejecución CLI pura
- Scrapy solo como último recurso (nunca dependencia única)
- API keys opcionales: si no están, el adaptador se marca `unavailable` y se excluye

---

## Criterios de éxito

- Todos los adaptadores sin API key funcionan sin configuración adicional
- El informe identifica al menos un proveedor `principal` por categoría (macro, mercados, cripto)
- La ejecución completa (`--providers all`) termina en menos de 5 minutos
- El código de cualquier adaptador puede copiarse al backend sin modificaciones estructurales
