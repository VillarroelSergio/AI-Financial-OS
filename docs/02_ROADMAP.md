# 02 - Roadmap

## Estado actual

AI Financial OS ya tiene una base funcional local-first con backend FastAPI,
desktop Tauri/React, core financiero, importacion CSV, inversiones, objetivos,
dashboard y una capa unificada de Market Intelligence.

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
