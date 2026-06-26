# 02 — Roadmap

## Estado de implementación

| Fase | Nombre | Estado | Commit(s) |
|------|--------|--------|-----------|
| 0 | Foundation | ✅ Completa | `e9f2fc9`..`ce21c51`, `20abbeb` |
| 1 | Financial Core MVP | ✅ Completa | `8861adf` |
| 2 | CSV Import Center | ✅ Completa | rama `feature/fase-2-import-center` |
| 3 | Investments Basic | ✅ Completa | rama `feature/fase-2-import-center` |
| 4 | Market Watch | ✅ Completa | rama `main` |
| 4.5 | Multi-Provider Market Data | ✅ Completa | rama `feat/multi-provider-market-data` |
| 4.7 | EOD Market Data | ✅ Completa | rama actual |
| 5 | Economic Intelligence | ✅ Completa | rama `feature/fase-5-economic-intelligence` |
| 5.5 | Market Intelligence Layer | ✅ Completa | rama `feature/fase-5.5-market-intelligence-layer` |
| 6 | Local AI Assistant | ⏳ Pendiente | — |
| 7 | Insights Engine | ⏳ Pendiente | — |
| 8 | Goals & Simulations | ⏳ Pendiente | — |
| 9 | Document Intelligence / RAG | ⏳ Pendiente | — |
| 10 | Hardening & Packaging | ⏳ Pendiente | — |

---

## Deudas técnicas

### Fase 1 — Financial Core MVP

| # | Deuda | Impacto | Bloquea |
|---|-------|---------|---------|
| TD-01 | `categories` sin `PATCH` ni `DELETE` — solo GET + POST implementados | Medio | Fase 2 (reimportación con categorías existentes) |
| TD-02 | Sin tests de integración para los módulos de Fase 1 (accounts, categories, transactions, dashboard) — solo existe `test_health.py` | Alto | Calidad general, refactors seguros |
| TD-03 | `ChartCard` no existe como componente independiente — Recharts se usa directamente en `SpendingPage` | Bajo | Consistencia del design system |

> Estas deudas no bloquean Fase 2, pero TD-02 debería resolverse antes de Fase 3 para evitar regresiones silenciosas.

### Fase 3 — Investments Portfolio Tracker

| # | Deuda | Impacto | Bloquea |
|---|-------|---------|---------|
| TD-04 | Conversión de divisas solo USD→EUR via yfinance `EURUSD=X` — otras divisas no soportadas | Medio | Multi-divisa en Fase 3+ |
| TD-05 | Sin histórico de precios — solo precio actual cacheado | Bajo | Gráfica histórica en Fase 4 |
| TD-06 | NAV de fondos Finizens siempre manual — sin proveedor automático | Bajo | No bloquea nada |

---

## Estrategia general

El proyecto se implementa por fases cerradas. Cada fase debe entregar una aplicación funcional, aunque sea limitada. No se debe avanzar a IA avanzada, RAG o automatización hasta que el core financiero sea estable.

## Fase 0 — Foundation ✅

### Objetivo

Crear la base técnica, documental y visual del proyecto.

### Incluye

- Monorepo inicial.
- Tauri + React + TypeScript.
- Backend FastAPI.
- SQLite.
- DuckDB integrado para analítica futura.
- Sistema de rutas frontend.
- Layout base con sidebar.
- Tema dark premium.
- Design tokens iniciales.
- Documentación en `/docs`.
- Scripts de desarrollo orquestados.

### No incluye

- IA.
- Importadores finales.
- RAG.
- APIs bancarias.
- Automatización.

### Resultado esperado

Aplicación de escritorio arrancando en local con navegación base, backend funcionando y pantalla inicial vacía.

---

## Fase 1 — Financial Core MVP ✅

### Objetivo

Construir el núcleo financiero determinista.

### Incluye

- CRUD de cuentas.
- CRUD de categorías.
- CRUD de movimientos.
- Modelo de ingresos/gastos.
- Cálculo de patrimonio básico.
- Cálculo de cashflow mensual.
- Dashboard Overview.
- Dashboard Spending.
- Estados vacíos cuidados.
- Datos mock opcionales para desarrollo.

### Pantallas

- Overview.
- Spending.
- Accounts.
- Transactions.
- Settings.

### Resultado esperado

El usuario puede crear cuentas, añadir movimientos manuales y ver métricas financieras básicas.

---

## Fase 2 — CSV Import Center ✅

### Objetivo

Importar datos personales mediante archivos CSV, empezando por Monefy.

### Incluye

- Import Center.
- Flujo de importación manual.
- Importador específico de Monefy.
- Vista previa del CSV.
- Mapeo de columnas.
- Validación de datos.
- Detección básica de duplicados.
- Confirmación antes de guardar.
- Historial de importaciones.
- Rollback de importación.

### Fuentes V1

- Monefy CSV.
- CSV genérico.

### Resultado esperado

El usuario puede importar el CSV de Monefy, revisar los movimientos, confirmar la importación y ver los dashboards actualizados.

---

## Fase 3 — Investments Basic ✅

### Objetivo

Añadir visión básica de inversiones.

### Incluye

- Cuentas de inversión.
- Activos manuales.
- Holdings manuales.
- Valor actual.
- Aportaciones.
- Rentabilidad simple.
- Distribución por activo.
- Dashboard Investments.

### Fuentes iniciales

- Trade Republic manual.
- Finizens manual.
- Cuenta remunerada manual.

### Resultado esperado

El usuario puede registrar posiciones básicas y ver su patrimonio financiero consolidado.

---

## Fase 4 — Market Watch ✅

### Objetivo

Añadir datos de mercado actualizados con caché local.

### Incluye

- Índices bursátiles.
- Divisas.
- Bonos 10 años.
- Caché local.
- Última actualización visible.
- Refresh manual.
- Gráficas simples.

### Activos previstos

- IBEX 35.
- Euro Stoxx 50.
- STOXX Europe 600.
- S&P 500.
- Nasdaq 100.
- Dow Jones.
- MSCI World.
- EUR/USD.
- Bono España 10Y.
- Bund 10Y.
- Treasury 10Y.

### Resultado esperado

El usuario puede consultar contexto de mercado desde la app sin mezclarlo con sus datos personales.

---

---

## Fase 4.5 — Multi-Provider Market Data ✅

### Objetivo

Sustituir el proveedor único (yfinance) por una arquitectura multi-provider gratuita
con máxima cobertura, caché DuckDB y señales de frescura de datos.

### Incluye

- **StooqProvider** — fuente primaria, sin API key, índices/forex/commodities/cripto/volatilidad.
- **YahooFinanceProvider** — fallback general, sin API key, marcado como fuente no garantizada.
- **AlphaVantageProvider** — opcional, API key gratuita (ALPHA_VANTAGE_API_KEY), acciones/forex/cripto.
- **FinnhubProvider** — opcional, API key gratuita (FINNHUB_API_KEY), acciones USA/forex/cripto/fundamentales.
- **FMPProvider** — opcional, API key gratuita (FMP_API_KEY), acciones/ETFs/perfiles/fundamentales.
- **ProviderRouter** — routing por asset_type, TTL por categoría, cross-validation, fallback en cascada.
- **DuckDB cache** — tablas `market_quotes_cache`, `market_candles_cache`, `market_provider_logs`, perfiles, fundamentales.
- **Modelos normalizados** — `MarketQuoteInternal`, `MarketCandle`, `CompanyProfile`, `Fundamentals`.
- **Freshness status** — live / fresh / delayed / eod / closed / stale / error / unknown.
- **Rate limiters** — por proveedor, respetando free tier.
- **UI actualizada** — `LiveIndicator` muestra estado real, `QuoteRow` muestra badge FB/CACHE, `change_absolute` desde servidor.
- **35 tests unitarios** — cobertura de providers, routing, caché, rate limiting, freshness.
- **`market_data_config.yaml`** — configuración declarativa de providers, routing, TTL y mappings de 36 activos.

### Restricciones cumplidas

- Ningún proveedor de pago.
- API keys nunca hardcodeadas (variables de entorno).
- No existe `ManualCsvProvider` ni importación CSV para mercados.
- "En vivo" solo cuando `freshness_status == "live"` — nunca asumido.
- App funciona sin API keys (Stooq + Yahoo).

### Documentación

- `docs/15_MARKET_PROVIDERS.md` — guía completa de proveedores.

---

## Fase 4.6 — Consensus Engine & TwelveData ✅

### Objetivo

Sustituir el fetch secuencial con fallback por un sistema de **fetch paralelo + motor de consenso**
que cruza los datos de múltiples proveedores para maximizar precisión. Yahoo Finance queda
relegado a último recurso. Se añade TwelveData como nuevo proveedor primario para forex y commodities.

### Incluye

- **TwelveDataProvider** — nuevo proveedor gratuito (800 req/día, 8 req/min). Primario para forex,
  commodities y validador para índices y cripto. API key: `TWELVEDATA_API_KEY`.
- **ConsensusEngine** (`consensus.py`) — motor de resolución de precio aislado y testeable:
  - **Estrategia D**: proveedor primario por asset_type con validadores en paralelo.
  - **Estrategia B**: mediana como precio de referencia cuando ≥3 proveedores disponibles.
  - **Estrategia C**: ponderación por proveedor × frescura × bonus primario × penalización fallback.
  - Detección y descarte de outliers con umbrales configurables por asset_type.
  - `confidence_score` final refleja calidad del consenso (0.0–1.0).
- **RequestBudget** (`budget.py`) — contador diario de peticiones por proveedor, backed en DuckDB.
  Alpha Vantage (400/día), TwelveData (700/día), FMP (200/día). Falla en abierto.
- **Fetch paralelo** — `ThreadPoolExecutor` en el router. Todos los providers se consultan
  simultáneamente, no en cascada. Timeout: 5 segundos por proveedor.
- **Yahoo como último recurso** — solo se invoca si `valid_provider_count == 0` tras el fetch paralelo.
  Nunca actúa como fuente primaria ni validador.
- **Routing declarativo** por `primary / validators / budget_aware / last_resort` en el YAML.
- **Logs de decisión estructurados** — cada resolución emite `selected_source`, `consensus_method`,
  `confidence_score`, `valid_provider_count`, `outliers`, `warnings`, `reason`.
- **Warnings normalizados** — `rate_limited`, `budget_exhausted`, `provider_error`, `provider_timeout`,
  `provider_mismatch`, `outlier_detected`, `unverified_single_provider`, `yahoo_last_resort`, `stale_cache_used`.
- **55 tests** — cobertura de ConsensusEngine (8 casos), RequestBudget (5), TwelveData (5),
  Router paralelo (2) y todos los tests anteriores (35).

### Primario por tipo de activo

| Tipo | Primario | Validadores | Último recurso |
|---|---|---|---|
| Índices | Stooq | TwelveData, Finnhub | Yahoo |
| Acciones USA | Finnhub | TwelveData, FMP | Yahoo |
| Acciones Europa | Stooq | TwelveData, FMP | Yahoo |
| Forex | TwelveData | Finnhub, AV | Yahoo |
| Cripto | Finnhub | TwelveData, AV | Yahoo |
| Commodities | TwelveData | — | Yahoo |
| Bonos | Stooq | — | Yahoo |
| Volatilidad | Stooq | — | Yahoo |

### Restricciones cumplidas

- Yahoo Finance nunca es fuente primaria ni validador.
- `TWELVEDATA_API_KEY` en `.env`, nunca en código.
- Ningún proveedor de pago.
- `MarketQuoteInternal` sin campos requeridos nuevos — contrato de API sin cambios.

### Documentación

- `docs/15_MARKET_PROVIDERS.md` — guía completa actualizada con TwelveData y ConsensusEngine.
- `docs/superpowers/specs/2026-06-24-market-data-consensus-engine-design.md` — spec técnico.
- `docs/superpowers/plans/2026-06-24-market-data-consensus-engine.md` — plan de implementación.

---

## Fase 4.7 — EOD Market Data ✅

### Objetivo

Simplificar el modelo de datos de mercado a cierre diario (EOD). Una única llamada al arranque, sin refresh manual, sin estados "live".

### Incluye

- `EodMarketService` — fetch secuencial Stooq al arrancar (background thread).
- `eod_only` mode en `ProviderRouter` — TTL 24h, pool filtrado a Stooq.
- `EodBadge` — sustituye `LiveIndicator`, muestra "Cierre DD/MM/YYYY".
- Eliminación del botón "Actualizar" en Market Watch.
- 6 tests unitarios cubriendo cache hit, cache miss, fallo, concurrencia y filtrado de providers.

---

## Fase 5 — Economic Intelligence ✅

### Objetivo

Incorporar datos macroeconómicos reales para España, Eurozona y EEUU.

### Incluye

- **FredProvider** — fuente principal de indicadores macro (inflación, subyacente, paro, PIB, tipos BCE/FED). API key gratuita: `FRED_API_KEY`.
- **StooqMacroProvider** — bridge sobre el ProviderRouter de Fase 4.6 para euríbor, bonos 10Y, índices y divisas.
- **DuckDB cache** — tabla `economic_indicators_cache` con TTL por categoría (4h para datos diarios, 24–48h para mensuales/trimestrales).
- **Modelos normalizados** — `IndicatorOut`, `RegionSnapshotOut`, `MacroSnapshotOut`, `PersonalImpactOut`.
- **4 endpoints REST** — `/snapshot`, `/indicators`, `/refresh`, `/impact`.
- **Vista de impacto personal (determinista, sin IA)** — 4 comparativas calculadas: inflación vs tasa de ahorro, tipo BCE vs liquidez, mercado vs cartera, poder adquisitivo.
- **EconomyPage** — snapshot global, tabs por región (España / Eurozona / EEUU), sección de impacto personal.
- **23 tests** — cobertura de FredProvider, repositorio, endpoints y cálculos de impacto.

### Proveedores

| Indicador | Fuente |
|-----------|--------|
| Inflación, subyacente, paro, PIB | FRED |
| Tipo BCE, Fed Funds | FRED |
| Euríbor 3M, Bonos 10Y | Stooq (vía ProviderRouter) |
| Índices, EUR/USD | Stooq (vía ProviderRouter) |

### Restricciones cumplidas

- `FRED_API_KEY` en `.env`, nunca en código.
- App funciona sin API key (indicadores macro muestran "no disponible"; índices y bonos funcionan vía Stooq).
- No se mezclan noticias ni calendarios macro.
- Siempre se muestra fecha de observación y fuente.

### Documentación

- `docs/superpowers/specs/2026-06-24-economic-intelligence-design.md` — spec técnico.

---

---

## Fase 5.5 — Market Intelligence Layer ✅

### Objetivo

Convertir el POC de datos de mercado (`market-data-poc/`) en un módulo de producción persistente que sirve como única fuente de verdad para la IA local.

### Incluye

- **Catálogo YAML** — 80+ indicadores declarativos organizados en 9 archivos (macro España, Europa, EEUU, divisas, bonos, commodities, mercados, energía, noticias). Define proveedor primario, secundario y fallback por indicador.
- **Adapters migrados** — 41 adapters del POC (9 España, 6 Europa, 7 USA, 13 Global, 1 RSS + `PublicDatasetAdapter`) con imports remapeados a `app.modules.market_intelligence.*`.
- **`ProviderOrchestrator`** — encadena primario → secundario → fallback por indicador, con traza del proveedor usado.
- **`QualityEngine`** — 5 checks ponderados: freshness (0.30), completeness (0.20), validity (0.25), outlier (0.15), provider_reliability (0.10). Score final 0.0–1.0.
- **DuckDB persistente** — 16 tablas `mi_*` (raw records, normalized records, market quotes, historical prices, macro observations, currency rates, bond yields, commodities, company profiles, news, provider health, quality checks, AI datasheets). Escrituras idempotentes con checksums MD5.
- **`AiDatasheetGenerator`** — genera un JSON compacto diario desde DuckDB (nunca desde proveedores live) para consumo exclusivo de la IA local.
- **API REST** — 6 endpoints bajo `/api/market-intelligence/*`: macro snapshot, quotes, forex, bonds, news, AI datasheet.
- **CLI** — 7 comandos `market:intelligence:*`: `init-db`, `update`, `quality`, `snapshot`, `datasheet`, `catalog`, `catalog:validate`.
- **48 tests** — migrations, modelos, catalog, adapter imports, orchestrator, quality engine, repository, API service, datasheet.

### Arquitectura

```txt
Catalog (YAML)
 └─ CatalogLoader → [CatalogIndicator ×80+]
      └─ ProviderOrchestrator
           └─ Adapter (primary → secondary → fallback)
                └─ AdapterResult
                     ├─ QualityEngine → QualityResult (score 0.0–1.0)
                     └─ Repository (DuckDB)
                          ├─ mi_raw_records (MD5 idempotency)
                          ├─ mi_normalized_records (composite key)
                          └─ mi_ai_datasheets
                               └─ AiDatasheetGenerator → AiDatasheetOut
                                    └─ /api/market-intelligence/ai-datasheet (Fase 6)
```

### Restricciones cumplidas

- DuckDB siempre vía singleton `get_duckdb()` — nunca `duckdb.connect()` directo.
- API keys desde `app.core.config.settings` — nunca `os.environ.get()`.
- Endpoints `/api/economy/*` existentes intactos (backward compat).
- Upserts con DELETE + INSERT (DuckDB no tiene `INSERT OR REPLACE`).
- Latest reads con `QUALIFY ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ... DESC) = 1`.

### Documentación

- `docs/superpowers/specs/2026-06-26-market-intelligence-layer-design.md` — spec técnico completo.
- `docs/superpowers/plans/2026-06-26-market-intelligence-fase55.md` — plan de implementación.

---

## Fase 6 — Local AI Assistant ⏳

### Objetivo

Integrar IA local mediante Ollama y LM Studio.

### Incluye

- Abstracción multi-provider.
- Provider Ollama.
- Provider LM Studio.
- Modelo inicial recomendado: Qwen.
- Panel lateral de IA.
- Tools financieras controladas.
- Respuestas basadas en datos reales.
- Citado interno de datos usados.
- Sin acceso SQL libre desde el modelo.

### Tools iniciales

- `get_net_worth`.
- `get_monthly_summary`.
- `get_spending_by_category`.
- `compare_periods`.
- `get_savings_rate`.
- `get_goal_progress`.
- `get_market_snapshot`.
- `get_macro_snapshot`.

### Resultado esperado

El usuario puede preguntar sobre sus datos y recibir explicaciones generadas localmente.

---

## Fase 7 — Insights Engine ⏳

### Objetivo

Convertir datos en insights sin depender completamente de IA.

### Incluye

- Motor determinista de insights.
- Detección de anomalías.
- Comparativas mensuales.
- Cambios relevantes.
- Alertas suaves.
- Resumen mensual.
- IA como redactor y explicador.

### Resultado esperado

La app empieza a avisar de cambios importantes sin que el usuario tenga que buscar manualmente.

---

## Fase 8 — Goals & Simulations ⏳

### Objetivo

Añadir objetivos financieros y simulaciones.

### Incluye

- Objetivos.
- Progreso.
- Fecha estimada.
- Simulación de ahorro mensual.
- Simulación de inversión mensual.
- Ajuste por inflación.
- Escenarios conservador/base/optimista.

### Resultado esperado

El usuario puede entender si está avanzando hacia sus objetivos y qué impacto tienen sus decisiones.

---

## Fase 9 — Document Intelligence / RAG ⏳

### Objetivo

Consultar documentación financiera mediante RAG local.

### Incluye

- Subida manual de documentos.
- Extracción de texto.
- ChromaDB.
- Embeddings locales.
- Preguntas sobre documentos.
- Enlaces entre documentos y entidades financieras.

### Documentos previstos

- Extractos.
- Informes fiscales.
- Contratos.
- Informes de broker.
- Declaraciones.

### Resultado esperado

El usuario puede consultar documentos financieros sin subirlos a la nube.

---

## Fase 10 — Hardening & Packaging ⏳

### Objetivo

Preparar la app para uso real diario.

### Incluye

- Empaquetado Windows.
- Backups.
- Exportación de datos.
- Cifrado opcional.
- Logs seguros.
- Migraciones robustas.
- Tests.
- Performance.
- Documentación de usuario.

### Resultado esperado

Aplicación instalable, estable y segura para uso personal continuado.
