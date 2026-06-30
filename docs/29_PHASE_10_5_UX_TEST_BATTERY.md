# 29 - Phase 10.5 UX Test Battery

## Estado

Fecha: 2026-06-30

Resultado: bateria automatizada ejecutada; QA manual end-to-end pendiente con datos reales.

## Evidencia automatizada

- Build frontend: `npm run build` correcto.
- Backend completo: `pytest app/tests` -> 189 passed.
- Snapshots UX desktop: 19/19.
- Snapshots UX responsive: 57/57 en desktop, tablet y mobile.

Snapshots generados:

- `overview.png`
- `spending.png`
- `investments.png`
- `investments-quality.png`
- `investments-empty.png`
- `goals.png`
- `economy.png`
- `insights.png`
- `imports-empty.png`
- `imports-preview.png`
- `settings.png`
- `markets.png`
- `markets-europa.png`
- `planificacion.png`
- `planificacion-recurrentes.png`
- `planificacion-facturas.png`
- `transactions.png`
- `assistant.png`
- `portfolio-import.png`

La herramienta tambien soporta variantes responsive con sufijos `-desktop`, `-tablet` y `-mobile`. No se deben regenerar snapshots sin confirmacion explicita del usuario.

## Matriz de pruebas

| Modulo | Caso | Estado | Evidencia |
|---|---|---|---|
| Resumen | Carga con datos mock/controlados | Automatizado | `overview.png` |
| Resumen | Datos reales/parciales | Pendiente manual | Requiere DB real |
| Gastos | Ranking y muchas categorias | Implementado | `SpendingPage`, `spending.png` |
| Gastos | Drilldown por categoria | Implementado | `ExpenseCategoryDetailDrawer` |
| Movimientos | Buscar por descripcion | Implementado | `TransactionsPage`, `transactions.png` |
| Movimientos | Filtros cuenta/categoria/fecha/tipo/importe | Implementado | `TransactionsPage` |
| Movimientos | Crear/editar/eliminar con confirmacion | Implementado | `TransactionsPage`, API transactions |
| Cuentas | Crear/editar/desactivar | Pendiente manual | Requiere recorrido con DB real |
| CSV | Preview/confirmacion/rollback | Implementado | `ImportsPage`, tests imports |
| CSV | CSV invalido | Automatizado backend | `test_imports.py` |
| Inversiones | Cartera/precios/manuales/sin precio | Implementado | `InvestmentsPage`, tests investments/price coverage |
| Calidad cartera | Confirmado/estimado/manual/no price/FX | Implementado | `ReconciliationTab`, `investments-quality.png`, `test_reconciliation.py` |
| Importar cartera | Texto fallback/manual/confirmar/cancelar/duplicados | Implementado | `PortfolioImportPage`, `test_portfolio_import.py` |
| Importar cartera | Captura real con OCR local | Fuera de alcance implementado | UI acepta capturas, no envia imagenes a terceros y comunica fallback de texto/manual |
| Economia | Espana/Eurozona/EEUU/parcial/ausente/impacto | Implementado | `EconomyPage`, market intelligence tests |
| Mercados | Cache/stale/proveedor fallando/error controlado | Implementado | `MarketsPage`, market intelligence tests |
| Objetivos | Simular/inflacion/aportacion/alcanzable/no alcanzable | Automatizado | `test_goals_simulation.py` |
| Planificacion | Presupuestos/recurrentes/calendario/cashflow | Automatizado | `test_budgets.py`, `test_recurring.py`, `test_cashflow.py` |
| Planificacion | Confirmar/ignorar recurrente candidato | Implementado | `RecurringTab`, `planificacion-recurrentes.png`, `GET /api/recurring/candidates` |
| Facturas hogar | Registrar/comparar/anomalias/estimar | Automatizado | `planificacion-facturas.png`, `test_household_bills.py` |
| Insights | Resumen/filtros/fuentes/descartar/incompletos | Automatizado | `test_insights_*.py` |
| Asistente IA | General/contextual/datos usados | Automatizado | `test_ai_assistant.py`, `assistant.png` |
| Asistente IA | Provider real local | Pendiente manual | Requiere Ollama/LM Studio arrancado |
| RAG | Subir/consultar/fuentes/sin resultados | Automatizado backend | `test_rag.py` |
| Ajustes | Idioma/moneda/IA/backups/integridad/ruta | Implementado | `SettingsPage`, `settings.png`, `test_security.py` |

## Limitaciones conocidas

- Los snapshots usan mock data y no sustituyen una sesion manual con datos reales.
- La extraccion OCR local de capturas de cartera no esta implementada; el producto comunica el alcance y no crea holdings desde imagen.
- El asistente IA contextual necesita provider local disponible para validar respuestas reales.
- La generacion responsive desktop/tablet/mobile queda soportada por tooling; la revision manual de esas imagenes queda como gate de Packaging.

## Criterio de salida recomendado

Antes de iniciar Packaging & Release:

1. Ejecutar una sesion manual con DB real.
2. Arrancar Ollama o LM Studio y validar preguntas contextuales en Gastos, Inversiones, Planificacion y Economia.
3. Confirmar si OCR local queda fuera de release o si debe bloquear Packaging.
4. Revisar visualmente snapshots existentes y resolver solapes; no regenerarlos sin confirmacion explicita.
