# 02 — Roadmap

## Estado de implementación

| Fase | Nombre | Estado | Commit(s) |
|------|--------|--------|-----------|
| 0 | Foundation | ✅ Completa | `e9f2fc9`..`ce21c51`, `20abbeb` |
| 1 | Financial Core MVP | ✅ Completa | `8861adf` |
| 2 | CSV Import Center | ⏳ Pendiente | — |
| 3 | Investments Basic | ⏳ Pendiente | — |
| 4 | Market Watch | ⏳ Pendiente | — |
| 5 | Economic Intelligence | ⏳ Pendiente | — |
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

## Fase 2 — CSV Import Center ⏳

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

## Fase 3 — Investments Basic ⏳

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

## Fase 4 — Market Watch ⏳

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

## Fase 5 — Economic Intelligence ⏳

### Objetivo

Incorporar datos macroeconómicos reales para España, Eurozona y EEUU.

### Incluye

- Inflación.
- Inflación subyacente.
- Paro.
- PIB.
- Tipos BCE.
- Tipos FED.
- Euríbor.
- Bonos 10 años.
- Comparativas España / Eurozona / EEUU.
- Gráficas históricas.
- Vista de impacto personal inicial sin IA.

### Resultado esperado

La app ofrece un snapshot económico limpio, actualizado y conectado conceptualmente con ahorro, gastos e inversiones.

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
