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
| 7 | Insights Engine | ⏳ Pendiente | — |
| 8 | Goals & Simulations | ⏳ Pendiente | — |
| 9 | Document Intelligence / RAG | ⏳ Pendiente | — |
| 10 | Hardening & Packaging | ⏳ Pendiente | — |

| Area | Estado | Ruta principal |
|---|---|---|
| Foundation | Completa | `scripts/`, `backend/`, `apps/desktop/` |
| Financial Core | Completa | `accounts`, `categories`, `transactions`, `dashboard` |
| Import Center | Completa | `backend/app/modules/imports` |
| Investments | Completa | `backend/app/modules/investments` |
| Goals | Completa | `backend/app/modules/goals` |
| Market Intelligence | Completa / evolucionando | `backend/app/modules/market_intelligence` |
| Local AI Assistant | Pendiente | `backend/app/modules/ai`, `backend/app/modules/rag` |
| Insights Engine | Pendiente | `backend/app/modules/insights` |
| Packaging | Pendiente | Tauri build/release |

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

## Proximas fases

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

### Fase 8 - Simulaciones y objetivos avanzados

Objetivo: ayudar al usuario a proyectar ahorro, inversion y objetivos.

Incluye:

- Escenarios conservador/base/optimista.
- Ajuste por inflacion.
- Progreso estimado por objetivo.
- Simulacion de aportaciones recurrentes.

### Fase 9 - Document Intelligence / RAG

Objetivo: consultar documentacion financiera local sin subirla a la nube.

Incluye:

- Subida manual de documentos.
- Extraccion de texto.
- Embeddings locales.
- Preguntas sobre documentos.
- Vinculo entre documentos y entidades financieras.

### Fase 10 - Hardening & Packaging

Objetivo: preparar la app para uso diario instalable.

Incluye:

- Empaquetado Windows.
- Backups/exportacion.
- Cifrado opcional.
- Logs seguros.
- Migraciones robustas.
- Tests de regresion.

## Deudas tecnicas

| ID | Deuda | Impacto |
|---|---|---|
| TD-01 | Revisar contrato real de `categories` frente a frontend y docs | Medio |
| TD-02 | Ampliar tests de integracion del core financiero | Alto |
| TD-03 | Consolidar docs de Market Intelligence con ejemplos de catalogo reales | Medio |
| TD-04 | Eliminar o archivar codigo POC cuando deje de aportar comparacion tecnica | Bajo |
| TD-05 | Definir CLI estable para comandos de Market Intelligence fuera del POC | Medio |

## Regla documental

La documentacion viva debe describir el codigo actual. Los planes generados, specs de
implementacion y briefs de agente son historico operativo: no deben mantenerse en la
raiz documental salvo que se conviertan en guia vigente.
