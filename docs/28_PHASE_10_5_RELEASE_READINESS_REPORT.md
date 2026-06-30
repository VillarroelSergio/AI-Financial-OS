# 28 - Phase 10.5 Release Readiness Report

## Evaluacion

Listo para Packaging & Release: no definitivo.

La fase 10.5 deja resueltos los bloqueantes principales de UX funcional, estados honestos y calidad de datos. Quedan limitaciones conocidas antes de declarar release final instalable.

## Problemas corregidos

- Mercados y economia usan estados controlados y no deben exponer errores crudos como experiencia principal.
- Movimientos ya permite busqueda, filtros por cuenta, categoria, fecha, tipo e importe, ordenacion, crear, editar y eliminar con confirmacion.
- Movimientos muestra nombres legibles de cuenta/categoria, no IDs internos.
- Calidad de cartera sustituye el naming tecnico de reconciliacion en la UI visible.
- Importar cartera acepta seleccion de capturas reales y comunica claramente que OCR local aun no esta activo; texto pegado y entrada manual siguen como fallback.
- Planificacion incorpora deteccion asistida de recurrentes sin conversion automatica.
- Planificacion incorpora facturas y suministros del hogar con comparativa, anomalias y estimacion del proximo recibo.
- Ajustes muestra estado de IA, provider/modelo, Ollama, LM Studio, RAG, documentos, backups, privacidad, integridad y ruta local.
- Copiloto IA contextual recibe modulo/ruta/metricas visibles con filtrado backend.
- Copiloto contextual pasa de overlay flotante a rail lateral para no tapar contenido en snapshots desktop.
- Shell responsive con navegacion superior movil/tablet y rail lateral del copiloto solo en desktop amplio.

## Modulos modificados

- Resumen y shell visual.
- Gastos.
- Movimientos.
- Inversiones.
- Importar cartera.
- Calidad de cartera.
- Economia.
- Mercados.
- Objetivos.
- Planificacion.
- Facturas hogar.
- Asistente IA.
- Ajustes.
- Snapshot UX tooling.

## Cambios de datos y calidad

- Nuevo endpoint `GET /api/recurring/candidates`.
- Nuevo modulo `household_bills` con CRUD y resumen.
- Nuevo modelo `HouseholdBill`.
- Contexto IA filtrado en `POST /api/ai/chat`.
- Documentacion de contratos actualizada.

## Bateria UX ejecutada

Snapshots desktop generados: 19/19.
Snapshots responsive generados: 57/57 en desktop, tablet y mobile.

- overview.png
- spending.png
- investments.png
- investments-quality.png
- investments-empty.png
- goals.png
- economy.png
- insights.png
- imports-empty.png
- imports-preview.png
- settings.png
- markets.png
- markets-europa.png
- planificacion.png
- planificacion-recurrentes.png
- planificacion-facturas.png
- transactions.png
- assistant.png
- portfolio-import.png

## Pruebas ejecutadas

- `npm run build`: correcto.
- `npm run snapshots:responsive`: 57/57 capturas.
- `pytest app/tests`: 189 passed.
- `pytest app/tests/test_portfolio_import.py app/tests/test_ai_assistant.py app/tests/test_household_bills.py app/tests/test_recurring.py`: 64 passed.
- `pytest app/tests/test_household_bills.py app/tests/test_recurring.py app/tests/test_cashflow.py`: 14 passed.
- `pytest app/tests/test_ai_assistant.py app/tests/test_household_bills.py app/tests/test_recurring.py`: 33 passed.

## Riesgos abiertos

- OCR local de capturas de cartera aun no implementado; la UI acepta archivos y comunica fallback.
- Facturas PDF/captura quedan como evolucion futura local-first.
- El copiloto contextual depende de provider local disponible.
- Snapshots usan mock data controlada; no sustituyen una QA manual con datos reales.
- No se deben regenerar snapshots sin confirmacion explicita.
- Hay warning de chunk grande en build Vite.

## Bloqueantes abiertos

- No hay bloqueante funcional P0 conocido en los cambios implementados.
- Release final requiere una pasada manual end-to-end con base de datos real y provider IA local arrancado.
- OCR local automatico de imagenes sigue fuera del alcance implementado; la alternativa soportada es captura aceptada + texto fallback + confirmacion manual.

## Resultado

Preparado para una QA final de Packaging & Release, no marcado como release final hasta completar la validacion manual end-to-end.
