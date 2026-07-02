# 02 - Roadmap

## Estado actual

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
| 6 | Local AI Assistant | ✅ Completa | rama `feat/phase-6-local-ai-assistant` |
| 6.4 | Data Integrity & Core UX Repair | En curso | rama `fix/phase-6-4-data-integrity-core-ux` |
| 7 | Insights Engine | ✅ Completa | rama `main` |
| 7.5 | Portfolio Import Assistant | ✅ Completa | rama `main` |
| 8 | Goals & Simulations | ✅ Completa | rama `main` |
| 8.5 | Portfolio Reconciliation & Investment Analytics | ✅ Completa | rama `feature/fase-8-5-portfolio-reconciliation` |
| 8.6 | Budgets, Recurring Transactions & Cashflow Planning | ✅ Completa | rama `feature/fase-8-6-budgets-cashflow` |
| 9 | Document Intelligence / RAG | Completa | rama actual |
| 10 | Hardening, Security & Backups | Completa | rama actual |
| 10.5 | UX Functional QA & Product Intelligence Repair | ✅ Completa | rama `feature/fase-10-5-ux-functional-qa-product-intelligence` |
| 10.6 | Release Candidate Stabilization | ✅ Completa | rama `fix/corrections-and-stabilization` |
| 11 | Packaging & Release | 🚀 En curso | — |

| Area | Estado | Ruta principal |
|---|---|---|
| Foundation | Completa | `scripts/`, `backend/`, `apps/desktop/` |
| Financial Core | Completa | `accounts`, `categories`, `transactions`, `dashboard` |
| Import Center | Completa | `backend/app/modules/imports` |
| Investments | Completa | `backend/app/modules/investments` |
| Goals | Completa | `backend/app/modules/goals` |
| Market Intelligence | Completa / evolucionando | `backend/app/modules/market_intelligence` |
| Local AI Assistant | Completa | `backend/app/modules/ai`, `backend/app/modules/rag` |
| Insights Engine | ✅ Completa | `backend/app/modules/insights` |
| Portfolio Reconciliation | Completa | `backend/app/modules/investments` |
| Budgets & Cashflow Planning | Completa / evolucionando | `backend/app/modules/budgets`, `backend/app/modules/recurring`, `backend/app/modules/cashflow` |
| Document Intelligence / RAG | Completa | `backend/app/modules/rag`, `backend/app/models/document.py` |
| Hardening, Security & Backups | Completa | `backend/app/modules/security`, base de datos, backups |
| UX Functional QA | ✅ Completa | `apps/desktop/src/features`, `backend/app/modules/market_intelligence`, docs fase 10.5 |
| Release Candidate Stabilization | ✅ Completa | `backend/app/modules/*`, `apps/desktop/src/features/*`, docs fase 10.6 |
| Packaging & Release | Pendiente | Tauri build/release |

## Capa vigente de mercado y macro

La ruta activa es `market_intelligence`. Sustituye la documentacion legacy basada en
`market_data`, `economic_data`, `/api/markets/*` y `/api/economy/*`.

Componentes actuales:

- Catalogo YAML en `backend/app/modules/market_intelligence/catalog/yaml/`.
- Ingestion adapters por region/proveedor.
- `ProviderOrchestrator` para primario, secundarios y fallback.
- `QualityEngine` para freshness, completeness, validity, outliers y fiabilidad.
- Persistencia DuckDB con tablas `mi_*`.
- API bajo `/api/market-intelligence/*`.
- Datasheet compacto para IA local.

## Detalle de fases completadas

### Fase 6.4 - Data Integrity & Core UX Repair

Objetivo: estabilizar la app base antes de Fase 7, evitando datos enganosos y mejorando las pantallas principales.

Incluye:

- Politica de datos mock/demo: deben marcarse como demo o excluirse de totales reales.
- Holdings normalizados: los UUID solo se usan como claves internas; si falta nombre se usa ticker y, si ambos faltan, "Activo sin identificar".
- CRUD basico de holdings con precio manual, cuenta/broker, divisa, sector y region.
- Market snapshot con secciones claras: indices, crypto, commodities, forex y bonds, con estado partial/empty/error y quality score.
- Estados empty/partial/error visibles en mercados, inversiones, cuentas, gastos y resumen.
- Porcentajes de gastos calculados como `importe_categoria / gasto_total * 100`.
- UX principal reforzada en Cuentas, Gastos, Inversiones y Resumen.

### Fase 6.4.1 - Expense Drilldown & Investment Price Refresh UX Fix

Incluye:

- Drill-down de gastos por categoria desde donut, barras y lista de gasto.
- Contrato `GET /api/dashboard/spending/category-detail` con total, porcentaje, media y movimientos.
- Detalle compatible con vista mensual y anual.
- Flujo de actualizacion de precios con resultado explicito: actualizados, manuales, omitidos y errores.
- Las cuentas remuneradas, efectivo y `savings_account` se omiten del precio manual porque usan saldo/balance.
- NAV queda reservado a fondos cuando exista un campo especifico; el copy general usa precio manual.

### Fase 6 - Local AI Assistant

Objetivo: integrar IA local mediante Ollama/LM Studio con tools controladas del backend.

Incluye:

- Provider local configurable.
- Panel de asistente en desktop.
- Tools financieras y de Market Intelligence.
- Respuestas con datos usados y periodo de referencia.
- Sin SQL libre generado por el modelo contra datos personales.

### Fase 7 - Insights Engine

Objetivo: generar insights deterministas antes de pasar por IA.

Incluye:

- Deteccion de anomalias.
- Comparativas mensuales.
- Alertas suaves.
- Resumen mensual.
- IA como redactora/explicadora, no como unica fuente de calculo.

### Fase 7.5 - Portfolio Import Assistant

Objetivo: permitir al usuario crear su cartera inicial desde capturas de pantalla o entrada manual.

Incluye:

- Parser local de texto pegado desde broker (Trade Republic, Degiro, etc.).
- Extracción de nombre, cantidad, valor actual, rentabilidad y divisa.
- Validación de identidad de instrumento (`resolve_asset()`).
- Cobertura de precios y FX (`audit_asset()`).
- Coste estimado desde rentabilidad: `valor / (1 + rentab/100)`.
- Tabla editable de revisión con estados: READY, REQUIRES_CONFIRMATION, NO_PRICE, MANUAL, REVIEW.
- Confirmación explícita obligatoria antes de crear holdings.
- Entrada rápida manual como fallback.
- Gestión de activos ambiguos (SpaceX/SPCX) y manuales.
- Sin envío de imágenes a servicios externos.

Documentación: `docs/20_PORTFOLIO_IMPORT_ASSISTANT.md`.

### Fase 8 - Simulaciones y objetivos avanzados

Objetivo: ayudar al usuario a proyectar ahorro, inversion y objetivos.

**✅ Implementado:**

- Escenarios conservador (2%)/base (6%)/optimista (10%) de crecimiento nominal anual.
- Ajuste por inflacion (configurable, defecto 3% anual).
- Progreso estimado por objetivo con fecha proyectada de consecucion.
- Simulacion de aportaciones recurrentes (capital inicial + aportacion mensual).
- Grafico de area con tres curvas solapadas y linea de referencia en objetivo.
- Panel expandible por objetivo con control deslizante de inflacion.
- Endpoints: `POST /api/goals/{id}/simulate` y `GET /api/goals/{id}/progress`.

Documentación: `docs/21_GOALS_SIMULATIONS.md`.

### Fase 8.5 - Portfolio Reconciliation & Investment Analytics

Objetivo: consolidar la cartera importada y asegurar que las posiciones, precios, divisas, costes estimados y valoraciones son fiables antes de usarlas en patrimonio, insights y simulaciones.

Incluye:

- Reconciliacion entre valor capturado, precio de mercado actualizado y valor calculado en EUR.
- Estado de calidad por holding: confirmado, estimado, manual, ambiguo, sin precio, FX pendiente o requiere revision.
- Separacion clara entre coste estimado desde captura, coste manual y coste confirmado.
- Rentabilidad no realizada por posicion y total de cartera.
- Peso por activo, divisa, region, sector, broker y tipo de activo.
- Deteccion de concentracion excesiva por activo o divisa.
- Control de activos manuales/no cotizados y su impacto sobre la valoracion total.
- Comparacion entre valor declarado/importado y valor calculado por mercado.
- Resumen de completitud de cartera: porcentaje valorado automaticamente, porcentaje manual y porcentaje pendiente de revision.
- Preparacion de datos de cartera para Insights Engine, Goals & Simulations e IA local.

Resultado esperado: el usuario sabe que parte de su cartera esta completamente validada, que parte usa datos estimados y que posiciones requieren accion manual.

Documentacion sugerida: `docs/22_PORTFOLIO_RECONCILIATION_ANALYTICS.md`.

### Fase 8.6 - Budgets, Recurring Transactions & Cashflow Planning

Objetivo: pasar del analisis historico a la planificacion mensual, permitiendo anticipar gastos, ingresos recurrentes, presupuestos y saldo esperado.

Incluye:

- Presupuestos por categoria y periodo.
- Gastos e ingresos recurrentes.
- Deteccion o alta manual de suscripciones.
- Calendario financiero simple con proximos cargos e ingresos.
- Prevision de cashflow mensual.
- Proyeccion de saldo a final de mes.
- Comparativa gasto real vs presupuesto.
- Alertas suaves por categorias cercanas al limite.
- Reglas para gastos fijos, variables, extraordinarios e inversiones recurrentes.
- Integracion con Insights Engine para avisos accionables.
- Integracion futura con IA local para explicaciones sobre presupuesto y cashflow.

Resultado esperado: el usuario puede responder cuanto puede gastar durante el mes, que cargos vienen proximamente y si mantiene su plan de ahorro.

Documentacion sugerida: `docs/23_BUDGETS_RECURRING_CASHFLOW.md`.

### Fase 9 - Document Intelligence / RAG

Objetivo: consultar documentacion financiera local sin subirla a la nube.

Implementado:

- Subida manual de documentos.
- Extraccion de texto.
- Embeddings locales deterministas.
- Preguntas sobre documentos con fuentes.
- Vinculo entre documentos y entidades financieras.
- Endpoints bajo `/api/rag`.

Documentacion: `docs/24_DOCUMENT_INTELLIGENCE_RAG.md`.

### Fase 10 - Hardening, Security & Backups

Objetivo: estabilizar la aplicacion para uso diario antes de empaquetarla, reforzando seguridad local, recuperacion de datos y calidad tecnica.

Implementado:

- Backups y exportacion de datos.
- Preparacion para cifrado local.
- Politica de logs seguros sin informacion financiera sensible.
- Validacion de integridad de base de datos.
- Tests de regresion de RAG, backups e integridad.
- Modo de recuperacion inicial mediante backups locales.
- Revision de permisos locales y rutas de datos.
- Politica clara de datos demo/mock frente a datos reales.

Documentacion: `docs/25_HARDENING_SECURITY_BACKUPS.md`.

### Fase 10.5 - UX Functional QA & Product Intelligence Repair

Objetivo: corregir bloqueantes de experiencia, estados de datos e inteligencia contextual antes de Packaging & Release.

Estado operativo:

| Punto | Estado | Evidencia |
|---|---|---|
| Product shell y UI polish | Hecho | `docs/27_FINANCIAL_COMMAND_CENTER_UI_POLISH.md`, shell y pantallas principales actualizadas |
| Mercados con estados honestos/cache/error controlado | Hecho | `apps/desktop/src/features/markets`, `backend/app/modules/market_intelligence` |
| Economia con calidad, regiones y datos no repetidos por fallback silencioso | Hecho | `apps/desktop/src/features/economy`, `backend/app/modules/market_intelligence/quality` |
| Calidad de cartera con explicacion de confianza, precios, FX y manuales | Hecho | UI visible como "Calidad de cartera", `backend/app/modules/investments/reconciliation_*` |
| Movimientos con busqueda, filtros, ordenacion, CRUD y sin UUID visibles | Hecho | `apps/desktop/src/features/transactions/TransactionsPage.tsx`, `backend/app/modules/transactions` |
| Importar cartera con capturas reales o alcance honesto, texto fallback y manual | Hecho parcial | UI acepta capturas y comunica OCR local pendiente; texto/manual y confirmacion explicita activos |
| Gastos con ranking, agrupacion "Otros", drilldown y visualizacion menos saturada | Hecho | `apps/desktop/src/features/spending`, `ExpenseCategoryDetailDrawer` |
| Objetivos con escenarios, inflacion y mensajes comprensibles | Hecho | `apps/desktop/src/features/goals`, `backend/app/modules/goals` |
| Planificacion con deteccion asistida de recurrentes | Hecho | `GET /api/recurring/candidates`, UI de candidatos, confirmacion/ignorar |
| Facturas y suministros del hogar | Hecho inicial | `backend/app/modules/household_bills`, `HouseholdBillsTab` |
| Copiloto IA contextual por modulo | Hecho | Contexto filtrado en `POST /api/ai/chat`, `contextualCopilot.ts` |
| Ajustes como centro de estado local | Hecho | IA/provider/modelo/RAG/documentos/backups/integridad/ruta local/privacidad visibles; crear backup desde UI |
| Bateria UX y snapshots | Hecho | `ux-snapshots/latest`, 19 rutas desktop y soporte responsive desktop/tablet/mobile |
| Informe release readiness | Hecho | `docs/28_PHASE_10_5_RELEASE_READINESS_REPORT.md` |
| Bateria de pruebas UX documentada | Hecho | `docs/29_PHASE_10_5_UX_TEST_BATTERY.md` |

Documentacion: `docs/27_FINANCIAL_COMMAND_CENTER_UI_POLISH.md`.

### Fase 10.6 - Release Candidate Stabilization ✅ Completa

Objetivo: corregir todos los bloqueantes P0/P1 identificados en el informe Release Readiness antes de avanzar a Packaging.

Veredicto: **GO para Fase 11** — todos los criterios cumplidos.

Corregido:

| Bloqueante | Módulo | Resolución |
|---|---|---|
| P0-01 | Importar cartera | Opción B implementada — captura marcada "Próximo", alcance honesto |
| P0-02 | Mercados | `DataStatusBadge` por fila; refresh manual con timestamp |
| P0-03 | Economía | FRED adapter aislado por `indicator_id`; `_first_not_none()` preserva 0.0 |
| P0-04 | Objetivos | `monthly_contribution_needed` calculado y mostrado; resumen textual por escenario |
| P0-05 | Asistente IA | Pre-flight health check; 503 honesto; AbortController 90s; sin carga infinita |
| P1-01 | Planificación | Auto-refresh tras crear presupuesto sin cambio de tab |
| UI | Transacciones | Picklist dark mode; cuenta no obligatoria en edición de Monify |

Pruebas: 206/206 backend tests, 0 errores TypeScript.


### Fase 11 - Packaging & Release 🚀 En curso

**Objetivo funcional:** entregar la aplicación como producto instalable para Windows, con arranque fiable, sin dependencias externas visibles para el usuario y con experiencia de primer uso clara.

**Alcance:**

- Empaquetado Windows con Tauri (`tauri build`): genera `.msi` / `.exe` instalable.
- Arranque coordinado: el proceso Tauri lanza el backend FastAPI + Uvicorn en proceso hijo, espera `GET /api/health` antes de abrir la ventana.
- Entorno de producción: variables de entorno y rutas de datos aisladas del entorno de desarrollo; DuckDB y SQLite en `%APPDATA%\FinancialAgent\`.
- Instalador y desinstalador limpios (sin residuos en `AppData` tras desinstalar salvo datos de usuario explícitamente conservados).
- Verificación post-build: smoke test automatizado que lanza el binario, espera UI, comprueba `/api/health` y cierra.
- Documentación de instalación, primer arranque y resolución de problemas comunes.
- Preparación de canal de actualización (auto-updater Tauri configurado para releases futuras).
- Revisión de tamaño final, tiempo de arranque (<5s en hardware típico) y experiencia de primer uso (onboarding mínimo viable).

**Implementado:**

- `backend/run_server.py` + `backend/financial-backend.spec`: backend compilado con PyInstaller (onedir) sin dependencia de Python instalado; datos en `%APPDATA%\FinancialAgent\` cuando corre empaquetado.
- `apps/desktop/src-tauri/src/lib.rs`: arranque coordinado — lanza el backend como proceso hijo, espera `/health` 200 antes de crear la ventana y lo termina al salir.
- `apps/desktop/src-tauri/tauri.conf.json`: targets `msi` + `nsis`, icono, backend como resource, CSP con puerto 8010, datos de usuario conservados al desinstalar.
- `scripts/build-release.ps1`: build completo (PyInstaller → resources → `tauri build`).
- `scripts/smoke-test.ps1`: verificación post-build (arranque, `/health`, tiempo, cierre sin huérfanos).
- Auto-updater documentado y diferido a la primera release pública (requiere claves de firma y endpoint de manifiestos).

Documentación: `docs/30_PACKAGING_RELEASE.md`.

**Criterios de aceptación:**

- [ ] `tauri build` produce instalador `.msi` sin errores.
- [ ] El instalador no requiere que el usuario instale Python, Node o ninguna dependencia adicional.
- [ ] La aplicación arranca en menos de 5 segundos en hardware de referencia (i5/8GB).
- [ ] `/api/health` responde `200` antes de que la ventana principal sea interactiva.
- [ ] Los datos del usuario persisten entre reinicios en `%APPDATA%\FinancialAgent\`.
- [ ] La desinstalación no deja residuos fuera de `%APPDATA%\FinancialAgent\` (datos del usuario se conservan por defecto).
- [ ] Smoke test automatizado pasa en build limpio.
- [ ] Documentación de instalación revisada y publicada.

**Limitaciones aceptadas heredadas de Fase 10.6:**

- Extracción automática de cartera desde captura de pantalla no disponible (comunicado como "Próximo" en UI).
- BLS adapter con el mismo gap de `indicator_id` que el FRED adapter pre-10.6 — diferido post-release.
- AbortController no limpiado en unmount de `useAiConversation` — sin impacto funcional confirmado.

## Deudas tecnicas

| ID | Deuda | Impacto |
|---|---|---|
| TD-01 | Revisar contrato real de `categories` frente a frontend y docs | Medio |
| TD-02 | Ampliar tests de integracion del core financiero | Alto |
| TD-03 | Consolidar docs de Market Intelligence con ejemplos de catalogo reales | Medio |
| TD-06 | Unificar estados del roadmap y areas funcionales cuando una fase cambie de estado | Medio |
| TD-07 | Consolidar modelo de holdings tras Portfolio Import Assistant: coste estimado, coste confirmado, instrumento validado, FX, precio actual y modo manual/automatico | Alto |
| TD-08 | BLS adapter: añadir `_INDICATOR_SERIES` mapping igual que `fred.py` — mismo gap de indicator_id-blindness corregido en Fase 10.6 | Medio |
| TD-09 | AbortController cleanup en `useEffect` return de `useAiConversation` — sin impacto funcional actual pero limpieza de recursos correcta | Bajo |

## Regla documental

La documentacion viva debe describir el codigo actual. Los planes generados, specs de
implementacion y briefs de agente son historico operativo: no deben mantenerse en la
raiz documental salvo que se conviertan en guia vigente.
