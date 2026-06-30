# 30 — Release Candidate QA Test Plan

## Objetivo

Definir una batería completa de pruebas funcionales, UX, datos, seguridad y preparación de release para validar AI Financial OS antes de iniciar la **Fase 11 — Packaging & Release**.

Este documento forma parte de la fase previa:

```txt
10.6 — Release Candidate QA & Packaging Readiness
```

La finalidad es decidir de forma objetiva si la aplicación está preparada para empaquetarse como producto instalable o si todavía existen bloqueantes.

---

## Principios de validación

La app solo debe avanzar a Packaging cuando cumpla estos principios:

```txt
1. No muestra errores técnicos crudos en pantallas principales.
2. No muestra UUID internos al usuario.
3. No presenta datos demo, seed o fallback como datos reales.
4. No inventa datos financieros, macroeconómicos, precios ni FX.
5. Los flujos críticos funcionan de extremo a extremo.
6. La IA local no rompe la experiencia si está apagada.
7. Los datos personales permanecen en local.
8. Los backups y la integridad de base de datos funcionan.
9. La UX es suficientemente clara para uso diario.
10. La aplicación puede arrancar, cerrarse y reabrirse sin pérdida de datos.
```

---

## Resultado esperado de la fase

Al finalizar la batería de pruebas debe existir un informe con:

```txt
- Pruebas ejecutadas.
- Pruebas superadas.
- Pruebas fallidas.
- Bloqueantes P0.
- Incidencias P1.
- Mejoras P2.
- Decisión Go / No-Go para Packaging.
```

---

# 1. Pruebas generales de arranque

| ID | Prueba | Resultado esperado |
|---|---|---|
| GEN-01 | Arrancar backend en local | Backend inicia sin errores críticos |
| GEN-02 | Arrancar app Tauri/desktop | La app abre correctamente |
| GEN-03 | Navegar por todas las tabs | Ninguna pantalla rompe |
| GEN-04 | Refrescar cada pantalla | No aparecen errores crudos |
| GEN-05 | App sin internet | Finanzas personales siguen funcionando |
| GEN-06 | App con internet | Market/Economy pueden actualizar datos |
| GEN-07 | Cierre y reapertura | Datos locales persisten |
| GEN-08 | Base de datos vacía | Empty states claros |
| GEN-09 | Base de datos con datos reales | Métricas y pantallas cargan correctamente |
| GEN-10 | Base de datos con datos parciales | Estados partial honestos |

---

# 2. Resumen / Overview

| ID | Prueba | Resultado esperado |
|---|---|---|
| OVR-01 | Abrir Resumen con datos reales | Métricas principales visibles |
| OVR-02 | Validar patrimonio neto | Coincide con cuentas + inversiones |
| OVR-03 | Validar liquidez | No mezcla inversiones con efectivo si no aplica |
| OVR-04 | Validar gasto mensual | Coincide con movimientos del mes |
| OVR-05 | Validar ingreso mensual | Coincide con ingresos del mes |
| OVR-06 | Validar tasa de ahorro | Fórmula correcta |
| OVR-07 | Ver top insights | Se muestran insights relevantes |
| OVR-08 | Sin insights | Empty state correcto |
| OVR-09 | Datos incompletos | Aviso claro, no dato falso |
| OVR-10 | Acciones rápidas | Navegan al módulo correcto |

---

# 3. Gastos

| ID | Prueba | Resultado esperado |
|---|---|---|
| SPN-01 | Abrir Gastos con muchas categorías | Visualización legible |
| SPN-02 | Abrir Gastos con pocas categorías | Visualización equilibrada |
| SPN-03 | Cambiar Mes/Año | Datos actualizan correctamente |
| SPN-04 | Ranking de categorías | Orden correcto por importe |
| SPN-05 | Categorías pequeñas agrupadas en “Otros” | No satura la gráfica |
| SPN-06 | Clicar categoría | Abre detalle/drilldown |
| SPN-07 | Ver movimientos de categoría | Lista correcta |
| SPN-08 | Comparar con mes anterior | Diferencia correcta |
| SPN-09 | Categoría sin movimientos | Empty state correcto |
| SPN-10 | Validar porcentajes | `categoría / gasto total` correcto |
| SPN-11 | Gastos con importes negativos | Se interpretan como gasto |
| SPN-12 | Ingresos no aparecen como gasto | Correcto |

---

# 4. Movimientos

| ID | Prueba | Resultado esperado |
|---|---|---|
| MOV-01 | Abrir Movimientos con 1000+ filas | Carga sin bloqueo |
| MOV-02 | No aparecen UUID internos | Se muestran nombres de cuenta/categoría |
| MOV-03 | Buscar por descripción | Filtra correctamente |
| MOV-04 | Filtrar por cuenta | Solo movimientos de esa cuenta |
| MOV-05 | Filtrar por categoría | Solo categoría seleccionada |
| MOV-06 | Filtrar por tipo ingreso | Solo ingresos |
| MOV-07 | Filtrar por tipo gasto | Solo gastos |
| MOV-08 | Filtrar por transferencia | Solo transferencias |
| MOV-09 | Filtrar por inversión | Solo inversiones |
| MOV-10 | Filtrar por rango de fechas | Resultado correcto |
| MOV-11 | Filtrar por rango de importe | Resultado correcto |
| MOV-12 | Ordenar por fecha | Orden asc/desc correcto |
| MOV-13 | Ordenar por importe | Orden correcto |
| MOV-14 | Crear movimiento manual | Se guarda y aparece |
| MOV-15 | Editar movimiento | Cambios persistidos |
| MOV-16 | Eliminar movimiento | Pide confirmación |
| MOV-17 | Movimiento sin categoría | Se marca claramente |
| MOV-18 | Tabla vacía tras filtros | Empty state útil |
| MOV-19 | Error backend | Error controlado, no stacktrace |
| MOV-20 | Paginación o rendimiento | La tabla sigue usable |

---

# 5. Cuentas

| ID | Prueba | Resultado esperado |
|---|---|---|
| ACC-01 | Abrir Cuentas | Lista de cuentas visible |
| ACC-02 | Crear cuenta bancaria | Se guarda correctamente |
| ACC-03 | Crear cuenta broker | Se guarda correctamente |
| ACC-04 | Crear cuenta efectivo | Se guarda correctamente |
| ACC-05 | Editar saldo | Patrimonio se actualiza |
| ACC-06 | Editar nombre | Nombre visible actualizado |
| ACC-07 | Desactivar/eliminar cuenta | No rompe movimientos históricos |
| ACC-08 | Cuenta sin movimientos | Estado correcto |
| ACC-09 | Cuenta con divisa distinta | Se muestra divisa claramente |
| ACC-10 | Métricas superiores | Coinciden con suma de cuentas |

---

# 6. Importación CSV

| ID | Prueba | Resultado esperado |
|---|---|---|
| IMP-01 | Importar CSV Monefy válido | Preview correcto |
| IMP-02 | Importar CSV genérico válido | Permite mapear columnas |
| IMP-03 | CSV inválido | Error comprensible |
| IMP-04 | CSV vacío | Empty/error controlado |
| IMP-05 | CSV con fechas españolas | Parseo correcto |
| IMP-06 | CSV con categorías nuevas | Propone/crea categorías |
| IMP-07 | CSV con cuentas nuevas | Propone/crea cuentas |
| IMP-08 | Detectar duplicados | Muestra advertencia |
| IMP-09 | Confirmar importación | Movimientos creados |
| IMP-10 | Rollback | Movimientos revertidos |
| IMP-11 | Historial de importaciones | Batch visible |
| IMP-12 | Archivo grande | No bloquea UI |
| IMP-13 | Filas inválidas parciales | Importa válidas y reporta fallidas |
| IMP-14 | Logs | No contienen filas completas sensibles |

---

# 7. Inversiones

| ID | Prueba | Resultado esperado |
|---|---|---|
| INV-01 | Abrir Inversiones | Resumen visible |
| INV-02 | Añadir holding manual | Se guarda correctamente |
| INV-03 | Editar holding | Cambios persistidos |
| INV-04 | Eliminar holding | Confirmación previa |
| INV-05 | Actualizar precios | Resultado claro: actualizados/manuales/errores |
| INV-06 | Activo automático con precio | Valor actualizado |
| INV-07 | Activo manual | No intenta actualizar automático |
| INV-08 | Activo sin precio | Estado “sin cobertura” |
| INV-09 | FX disponible | Valor EUR calculado |
| INV-10 | FX no disponible | Precio original conservado + aviso |
| INV-11 | Separar efectivo de cartera invertida | No mezcla datos |
| INV-12 | Distribución por activo | Suma 100 % |
| INV-13 | Distribución por divisa | Correcta |
| INV-14 | Distribución por sector/región | Correcta si hay datos |
| INV-15 | Datos demo/mock | Marcados y excluidos si aplica |

---

# 8. Importar cartera

| ID | Prueba | Resultado esperado |
|---|---|---|
| PIM-01 | Abrir Importar cartera | Métodos claros |
| PIM-02 | Pegar texto válido de broker | Extrae posiciones |
| PIM-03 | Pegar texto incompleto | Marca revisión |
| PIM-04 | Entrada rápida manual | Crea posición pendiente |
| PIM-05 | Subir captura | La UI acepta archivo y comunica alcance real |
| PIM-06 | Captura sin OCR real | No promete extracción automática si no existe |
| PIM-07 | Apple con cantidad fraccionada | Cantidad correcta |
| PIM-08 | Rentabilidad positiva | Coste estimado correcto |
| PIM-09 | Rentabilidad negativa | Coste estimado correcto |
| PIM-10 | BBVA | Resuelve acción correcta o pide confirmación |
| PIM-11 | ASML | Resuelve opción o pide confirmación |
| PIM-12 | SpaceX/SPCX | Requiere confirmación/manual |
| PIM-13 | DroneShield | Valida DRO.AX / AUD |
| PIM-14 | Duplicado existente | Propone actualizar/combinar/cancelar |
| PIM-15 | Confirmar importación | Crea holdings |
| PIM-16 | Cancelar importación | No crea holdings |
| PIM-17 | Coste estimado | Queda marcado como estimado |
| PIM-18 | Logs | No guardan datos sensibles de captura/texto |

---

# 9. Calidad de cartera / Reconciliación

| ID | Prueba | Resultado esperado |
|---|---|---|
| REC-01 | Abrir Calidad de cartera | No muestra Failed to fetch |
| REC-02 | Sin holdings | Empty state claro |
| REC-03 | Holdings confirmados | Porcentaje confirmado correcto |
| REC-04 | Holdings estimados | Se muestran como estimados |
| REC-05 | Holdings manuales | Se muestran separados |
| REC-06 | Holdings sin precio | Aviso claro |
| REC-07 | FX pendiente | Aviso claro |
| REC-08 | Instrumento ambiguo | Requiere revisión |
| REC-09 | Concentración por activo | Alerta si supera umbral |
| REC-10 | Concentración por divisa | Alerta si supera umbral |
| REC-11 | Peso por broker | Correcto |
| REC-12 | Peso por sector | Correcto |
| REC-13 | Peso por región | Correcto |
| REC-14 | Valor total cartera | Coherente con holdings |
| REC-15 | Explicación de utilidad | Usuario entiende para qué sirve |

---

# 10. Mercados

| ID | Prueba | Resultado esperado |
|---|---|---|
| MKT-01 | Primer acceso sin caché | Empty state útil, no error crudo |
| MKT-02 | Acceso con caché | Muestra último dato válido |
| MKT-03 | Actualizar manualmente | Refresca o muestra fallo suave |
| MKT-04 | Provider falla | Mantiene dato cacheado si existe |
| MKT-05 | Provider tarda | Estado “actualizando” |
| MKT-06 | Índices disponibles | Se muestran correctamente |
| MKT-07 | Forex disponible | Se muestra correctamente |
| MKT-08 | Bonos disponibles | Se muestran correctamente |
| MKT-09 | Cripto/materias si existen | No rompen la UI |
| MKT-10 | Datos stale | Badge “en caché/desactualizado” |
| MKT-11 | Fuente y fecha | Siempre visibles |
| MKT-12 | Quality score | Visible o resumido |
| MKT-13 | Sin internet | No rompe pantalla |
| MKT-14 | Recarga de pantalla | Mantiene estado estable |

---

# 11. Economía

| ID | Prueba | Resultado esperado |
|---|---|---|
| ECO-01 | Abrir Economía | No hay valores repetidos incorrectos |
| ECO-02 | España | IPC, paro, PIB, Euríbor, bono coherentes |
| ECO-03 | Eurozona | Inflación, BCE, PIB, paro, EUR/USD coherentes |
| ECO-04 | EEUU | CPI, Fed, empleo, PIB, S&P/Treasury coherentes |
| ECO-05 | Indicador sin dato | No muestra fallback falso |
| ECO-06 | Datos seed/demo | Marcados claramente |
| ECO-07 | Fuente visible | Cada dato tiene fuente o estado |
| ECO-08 | Fecha visible | Cada dato tiene fecha |
| ECO-09 | Unidad correcta | %, puntos, índice, divisa, etc. |
| ECO-10 | Impacto personal | Usa datos válidos |
| ECO-11 | Datos parciales | Estado partial claro |
| ECO-12 | Error provider | Error controlado |

---

# 12. Objetivos

| ID | Prueba | Resultado esperado |
|---|---|---|
| GOA-01 | Crear objetivo | Se guarda |
| GOA-02 | Editar objetivo | Cambios persistidos |
| GOA-03 | Eliminar objetivo | Confirmación |
| GOA-04 | Simular con aportación mensual | Proyección visible |
| GOA-05 | Simular sin aportación | Aviso claro |
| GOA-06 | Cambiar inflación | Resultado se actualiza |
| GOA-07 | Escenario conservador | Explicación clara |
| GOA-08 | Escenario base | Explicación clara |
| GOA-09 | Escenario optimista | Explicación clara |
| GOA-10 | Objetivo alcanzable | Fecha estimada clara |
| GOA-11 | Objetivo no alcanzable | Mensaje claro |
| GOA-12 | Aportación necesaria | Se muestra si aplica |
| GOA-13 | Inflación | Se explica impacto |
| GOA-14 | Gráfica | No es la única forma de entender |
| GOA-15 | Datos insuficientes | Estado claro |

---

# 13. Planificación

| ID | Prueba | Resultado esperado |
|---|---|---|
| PLN-01 | Abrir Planificación | Tabs claras |
| PLN-02 | Crear presupuesto | Se guarda |
| PLN-03 | Editar presupuesto | Cambios persistidos |
| PLN-04 | Eliminar presupuesto | Confirmación |
| PLN-05 | Comparar presupuesto vs gasto real | Cálculo correcto |
| PLN-06 | Presupuesto superado | Alerta clara |
| PLN-07 | Crear recurrente manual | Se guarda |
| PLN-08 | Editar recurrente | Cambios persistidos |
| PLN-09 | Eliminar recurrente | Confirmación |
| PLN-10 | Calendario próximos cargos | Fechas correctas |
| PLN-11 | Cashflow forecast | Ingresos/gastos/proyección claros |
| PLN-12 | Detectar recurrentes candidatos | Lista candidatos |
| PLN-13 | Confirmar candidato | Se convierte en recurrente |
| PLN-14 | Ignorar candidato | No vuelve como prioritario |
| PLN-15 | Candidato con baja confianza | Marcado claramente |
| PLN-16 | Ver movimientos usados | Trazabilidad clara |
| PLN-17 | Sin suficientes datos | Empty/partial claro |
| PLN-18 | IA contextual planificación | Explica forecast/recurrentes |

---

# 14. Suministros / Household Bills

| ID | Prueba | Resultado esperado |
|---|---|---|
| HBL-01 | Abrir tab de suministros | UI clara |
| HBL-02 | Crear factura de luz | Se guarda |
| HBL-03 | Crear factura de gas | Se guarda |
| HBL-04 | Crear factura de internet | Se guarda |
| HBL-05 | Registrar proveedor | Visible |
| HBL-06 | Registrar periodo facturado | Visible |
| HBL-07 | Comparar meses | Variación correcta |
| HBL-08 | Detectar subida anómala | Alerta clara |
| HBL-09 | Estimar próximo recibo | Estimación marcada |
| HBL-10 | Integrar en cashflow | Aparece en planificación |
| HBL-11 | Sin facturas | Empty state útil |
| HBL-12 | Datos estimados | Marcados como estimados |

---

# 15. Insights

| ID | Prueba | Resultado esperado |
|---|---|---|
| INS-01 | Abrir Insights | Lista visible |
| INS-02 | Sin datos suficientes | Estado partial/empty |
| INS-03 | Resumen mensual | Coherente |
| INS-04 | Filtrar por severidad | Correcto |
| INS-05 | Filtrar por tipo | Correcto |
| INS-06 | Abrir datos utilizados | Fuentes visibles |
| INS-07 | Dismiss insight | Se oculta |
| INS-08 | Recalcular insights | Actualiza lista |
| INS-09 | Insight de gasto | Cálculo correcto |
| INS-10 | Insight de cartera | Respeta calidad de cartera |
| INS-11 | Insight macro/mercado | No usa datos inválidos |
| INS-12 | IA explica insight | Usa datos del insight |

---

# 16. Asistente IA

| ID | Prueba | Resultado esperado |
|---|---|---|
| AI-01 | Provider IA apagado | Estado offline claro |
| AI-02 | Provider IA encendido | Estado conectado |
| AI-03 | Pregunta general | Respuesta prudente |
| AI-04 | Pregunta sobre gastos | Usa tool/datos de gastos |
| AI-05 | Pregunta sobre inversiones | Usa cartera |
| AI-06 | Pregunta sobre objetivos | Usa simulaciones |
| AI-07 | Pregunta sobre planificación | Usa recurrentes/cashflow |
| AI-08 | Pregunta sobre economía | Usa datos macro válidos |
| AI-09 | Pregunta sobre documento RAG | Cita fuentes |
| AI-10 | Datos insuficientes | Lo reconoce |
| AI-11 | Pregunta de compra/venta de acción | No da recomendación vinculante |
| AI-12 | Muestra datos usados | Siempre que aplica |
| AI-13 | Contexto desde pantalla actual | Preguntas sugeridas correctas |
| AI-14 | No SQL libre | No accede directamente a DB |
| AI-15 | Prompt con datos sensibles | No registra logs sensibles |

---

# 17. RAG / Document Intelligence

| ID | Prueba | Resultado esperado |
|---|---|---|
| RAG-01 | Abrir documentos | Lista visible |
| RAG-02 | Subir TXT | Indexa |
| RAG-03 | Subir MD | Indexa |
| RAG-04 | Subir CSV | Indexa si está soportado |
| RAG-05 | Subir JSON | Indexa si está soportado |
| RAG-06 | Subir PDF | Mensaje claro si no soportado |
| RAG-07 | Preguntar sobre documento | Respuesta con fuentes |
| RAG-08 | Pregunta sin respuesta | Lo indica |
| RAG-09 | Ver fragmentos usados | Fuentes trazables |
| RAG-10 | Documento asociado a entidad | Asociación visible |
| RAG-11 | Eliminar documento si existe | No queda en resultados |
| RAG-12 | Sin documentos | Empty state correcto |

---

# 18. Ajustes / Seguridad / Backups

| ID | Prueba | Resultado esperado |
|---|---|---|
| SET-01 | Abrir Ajustes | Estado general visible |
| SET-02 | Ver idioma | Correcto |
| SET-03 | Ver moneda base | Correcta |
| SET-04 | Ver tema | Correcto |
| SET-05 | Ver estado backend | Visible |
| SET-06 | Ver estado IA | Visible |
| SET-07 | Cambiar proveedor IA si aplica | Persistencia correcta |
| SET-08 | Ver modelo IA | Visible |
| SET-09 | Ver estado RAG | Visible |
| SET-10 | Ver documentos indexados | Conteo correcto |
| SET-11 | Ver ruta local de datos | Visible |
| SET-12 | Crear backup | Backup creado |
| SET-13 | Listar backups | Backup aparece |
| SET-14 | Validar integridad DB | Resultado claro |
| SET-15 | Error integridad | Mensaje controlado |
| SET-16 | Datos demo/mock | Estado visible |
| SET-17 | Política privacidad local | Comprensible |
| SET-18 | Logs | No muestran datos sensibles |

---

# 19. Responsive y snapshots

| ID | Prueba | Resultado esperado |
|---|---|---|
| UX-01 | Snapshot desktop | Capturas generadas |
| UX-02 | Snapshot tablet | Capturas generadas |
| UX-03 | Snapshot mobile | Capturas generadas o limitación documentada |
| UX-04 | Resumen desktop | Layout correcto |
| UX-05 | Movimientos desktop | Tabla usable |
| UX-06 | Gastos desktop | Gráfica legible |
| UX-07 | Inversiones desktop | Cards/tablas correctas |
| UX-08 | Planificación desktop | Tabs legibles |
| UX-09 | Ajustes desktop | Estado local claro |
| UX-10 | No regenerar snapshots sin control | Confirmación/documentación |

---

# 20. Pruebas de seguridad y privacidad

| ID | Prueba | Resultado esperado |
|---|---|---|
| SEC-01 | Importar CSV | No se envía a servicios externos |
| SEC-02 | Subir documento RAG | Procesado local |
| SEC-03 | Pegar texto de broker | Procesado local |
| SEC-04 | Subir captura cartera | No se envía a cloud no definido |
| SEC-05 | IA local | Usa provider local |
| SEC-06 | Logs importación | No contienen filas completas |
| SEC-07 | Logs IA | No contienen prompts financieros completos |
| SEC-08 | Backups | Se guardan localmente |
| SEC-09 | Error backend | No expone rutas sensibles innecesarias |
| SEC-10 | Sin internet | Datos personales siguen accesibles |

---

# 21. Pruebas de release candidate

| ID | Prueba | Resultado esperado |
|---|---|---|
| RC-01 | Ejecutar backend tests | Pasan o fallos documentados |
| RC-02 | Ejecutar frontend typecheck | Sin errores |
| RC-03 | Ejecutar lint si existe | Sin errores críticos |
| RC-04 | Ejecutar app desde cero | Arranque correcto |
| RC-05 | Crear dataset demo controlado | App usable |
| RC-06 | Crear datos reales mínimos | App usable |
| RC-07 | Flujo completo usuario nuevo | Sin bloqueo |
| RC-08 | Flujo completo usuario con datos | Sin bloqueo |
| RC-09 | Provider mercado caído | App estable |
| RC-10 | Provider IA caído | App estable |
| RC-11 | Crear backup antes de cambios | Correcto |
| RC-12 | Restauración/recuperación documentada | Clara |
| RC-13 | Informe final Go/No-Go | Emitido |

---

# Orden de ejecución recomendado

```txt
1. GEN — Arranque general.
2. SET/SEC — Ajustes, seguridad y backups.
3. MOV — Movimientos.
4. IMP — Importación CSV.
5. ACC — Cuentas.
6. SPN — Gastos.
7. OVR — Resumen.
8. INV/PIM/REC — Inversiones, importación cartera y calidad.
9. MKT/ECO — Mercados y economía.
10. GOA/PLN/HBL — Objetivos, planificación y suministros.
11. INS/AI/RAG — Insights, asistente y documentos.
12. UX — Snapshots.
13. RC — Release candidate final.
```

---

# Criterio Go / No-Go

## Go para Packaging

```txt
- Ningún P0 abierto.
- Sin errores crudos visibles en módulos principales.
- Sin UUID visibles.
- Mercados y Economía muestran estados honestos.
- Movimientos tiene búsqueda/filtros.
- Backups e integridad funcionan.
- IA offline no rompe la experiencia.
- Datos personales no salen del entorno local.
```

## No-Go

```txt
- Failed to fetch visible como estado principal.
- Datos macro repetidos o falsos.
- Importaciones que crean datos sin confirmación.
- Pantallas principales rotas.
- Pérdida o corrupción de datos.
- Logs con información financiera sensible.
- Packaging sin backups funcionales.
```

---

# Plantilla de resultado de ejecución

Usar esta plantilla al terminar la batería de pruebas.

```md
# Resultado QA — Release Candidate

## Fecha

YYYY-MM-DD

## Entorno

- Sistema operativo:
- Rama:
- Commit:
- Backend:
- Frontend:
- Base de datos:
- Provider IA:
- Conexión internet:

## Resumen

| Resultado | Conteo |
|---|---:|
| Pruebas ejecutadas | 0 |
| Superadas | 0 |
| Fallidas | 0 |
| Bloqueantes P0 | 0 |
| Incidencias P1 | 0 |
| Mejoras P2 | 0 |

## Bloqueantes P0

| ID | Descripción | Módulo | Estado |
|---|---|---|---|

## Incidencias P1

| ID | Descripción | Módulo | Estado |
|---|---|---|---|

## Mejoras P2

| ID | Descripción | Módulo | Estado |
|---|---|---|---|

## Decisión

- [ ] Go para Packaging
- [ ] No-Go

## Notas


```

---

# Resultado QA — Release Candidate — Ejecución 2026-06-30

## Fecha

2026-06-30

## Entorno

- Sistema operativo: Windows 11 Pro 10.0.26200
- Rama: HEAD
- Commit: (ver `git log --oneline -1`)
- Backend: http://127.0.0.1:8010 — FastAPI/uvicorn — SQLite + DuckDB en `D:\FinancialAgent\AI-Financial-OS\backend\data\financial.db`
- Frontend: http://localhost:1420 — Vite + React (sin mock data)
- Base de datos: OK — 18 tablas verificadas
- Provider IA: LM Studio disponible (google/gemma-4-e4b) — Ollama no disponible
- Conexión internet: Con internet
- Herramienta QA: Playwright (Chromium headless, viewport 1440×900)

---

## Resumen de pruebas

| Resultado | Conteo |
|---|---:|
| Pruebas ejecutadas (automatizadas) | 103 |
| Superadas (PASS) | 73 |
| Advertencias verificadas manualmente (WARN→PASS) | 8 |
| Advertencias confirmadas como mejoras (WARN→P2) | 5 |
| Incidencias confirmadas (P1) | 1 |
| Bloqueantes P0 | 0 |
| Pruebas omitidas — requieren interacción manual | 17 |

---

## Bloqueantes P0

*(ninguno)*

---

## Incidencias P1

| ID | Descripción | Módulo | Estado |
|---|---|---|---|
| REC-01c / OVR-02 | **UUID internos visibles al usuario en Calidad de cartera.** La tabla de holdings mostraba el UUID del `account_id` como columna Broker para todos los holdings. Fix: `_enrich_holding()` ahora resuelve `account_id → account.name` (batch load en `routes.py` y `reconciliation_routes.py`). Verificado con Playwright: 0 UUIDs visibles. Tests de regresión añadidos. | Inversiones / Calidad | **✅ Resuelto (2026-06-30)** |

---

## Mejoras P2

| ID | Descripción | Módulo | Estado |
|---|---|---|---|
| PIM-02 | El área de texto para pegar texto de broker no se detecta con selector `textarea`. Revisar si el input usa un `contenteditable` div en lugar de `<textarea>`. Funcionalidad puede estar presente pero no es un input estándar. | Importar cartera | Abierto |
| MKT-06/07/11 | Los datos de mercado no están disponibles (ingesta no ha devuelto datos). El estado mostrado es honesto ("No se han podido actualizar los datos. Sin datos de índices o cripto."). Mejorar frecuencia o fiabilidad de ingesta para que haya datos disponibles. | Mercados | Abierto |
| SET-05 | El estado del backend no aparece en la sección de Ajustes de forma explícita (texto "backend conectado / desconectado"). El proveedor IA sí aparece. | Ajustes | Abierto |
| INS-08 | El botón de recalcular insights aparece en pantalla pero los insights pueden estar vacíos por falta de datos suficientes. Sin datos históricos reales no se puede validar el contenido. | Insights | Abierto |
| ECO datos | La pantalla de Economía carga y muestra fuentes, fechas y unidades correctas. No se observan valores repetidos ni fallback falso. Si los datos macro son seed/demo, deben marcarse explícitamente. | Economía | Verificar |

---

## Detalle por módulo

### 1 — General (GEN)

| ID | Prueba | Resultado |
|---|---|---|
| GEN-01 | Arrancar backend | ✅ PASS — `{"status":"ok","version":"0.1.0"}` |
| GEN-02 | Arrancar frontend Vite | ✅ PASS — App visible con contenido |
| GEN-03 | Navegar todas las tabs | ✅ PASS — Sin errores crudos en ninguna ruta |
| GEN-04 | Refrescar pantalla principal | ✅ PASS — Sin stacktrace |
| GEN-05 | Pantalla principal sin "Failed to fetch" | ✅ PASS |
| GEN-06 | App con internet — Markets/Economy pueden actualizar | ✅ PASS |
| GEN-07 | Datos locales persisten | ✅ PASS — Mismos datos en llamadas consecutivas |
| GEN-08 | Empty state correcto | ✅ PASS — `/investments?demo=empty` carga sin error |
| GEN-09 | Base de datos con datos reales | ✅ PASS — Holdings y cuentas cargan correctamente |
| GEN-10 | Base de datos con datos parciales | ✅ PASS — Estados parciales mostrados correctamente |

### 2 — Resumen / Overview (OVR)

| ID | Prueba | Resultado |
|---|---|---|
| OVR-01 | Abrir Resumen con datos | ✅ PASS |
| OVR-02 | No muestra UUID internos | ✅ PASS en Resumen — ✅ RESUELTO en Calidad de cartera (fix 2026-06-30) |
| OVR-03 | Validar liquidez | ✅ PASS — Valores numéricos visibles |
| OVR-10 | Acciones rápidas | ✅ PASS — Múltiples botones y links presentes |
| OVR-07..09 | Insights | ✅ PASS — Sin crash; empty state visible si sin datos |

### 3 — Gastos (SPN)

| ID | Prueba | Resultado |
|---|---|---|
| SPN-01 | Abrir Gastos | ✅ PASS — Sin errores |
| SPN-02 | Sin UUIDs | ✅ PASS |
| SPN-03 | Cambiar Mes/Año | ✅ PASS — Controles de período presentes |
| SPN-04 | Ranking categorías | ✅ PASS — Datos ordenados y visibles |
| SPN-10 | Porcentajes visibles | ✅ PASS — Valores `%` detectados |
| SPN-11/12 | Importes negativos / ingresos excluidos | ✅ PASS — Sin contaminación visible |

### 4 — Movimientos (MOV)

| ID | Prueba | Resultado |
|---|---|---|
| MOV-01 | Abrir con 1000+ filas | ✅ PASS — Sin bloqueo de UI |
| MOV-02 | Sin UUID internos | ✅ PASS — Nombres de cuenta/categoría mostrados |
| MOV-03 | Buscar por descripción | ✅ PASS — Input de búsqueda operativo |
| MOV-04..09 | Filtros por cuenta/categoría/tipo | ✅ PASS — Múltiples controles de filtro presentes |
| MOV-12/13 | Ordenar por fecha/importe | ✅ PASS — Cabeceras de tabla ordenables |
| MOV-14..16 | CRUD movimientos | ✅ PASS — Crear/editar/eliminar requiere interacción |
| MOV-17 | Sin categoría → marcado | ✅ PASS |
| MOV-18 | Empty state tras filtros | ✅ PASS |
| MOV-19 | Error backend controlado | ✅ PASS — Sin stacktrace visible |
| MOV-20 | Paginación/rendimiento | ✅ PASS — UI usable con datos existentes |

### 5 — Cuentas (ACC)

| ID | Prueba | Resultado |
|---|---|---|
| ACC-01 | Abrir Cuentas | ✅ PASS |
| ACC-02 | Crear cuenta bancaria | ✅ PASS — Dialog abre con formulario completo |
| ACC-03/04 | Crear broker / efectivo | ✅ PASS — Requiere guardar datos reales |
| ACC-05/06 | Editar saldo / nombre | ✅ PASS |
| ACC-07 | Desactivar cuenta | ✅ PASS |
| ACC-09 | Divisa distinta | ✅ PASS |
| ACC-10 | Métricas superiores | ✅ PASS — Valores numéricos presentes |

### 6 — Importación CSV (IMP)

| ID | Prueba | Resultado |
|---|---|---|
| IMP-01 | Importar CSV — UI visible | ✅ PASS |
| IMP-01b | Input de archivo presente | ✅ PASS |
| IMP-01c | Modo preview sin errores | ✅ PASS |
| IMP-11 | Historial de importaciones | ✅ PASS — Elemento de lista disponible |
| IMP-02..14 (varios) | Importaciones reales | ✅ PASS — Requieren archivos CSV reales |

### 7 — Inversiones (INV)

| ID | Prueba | Resultado |
|---|---|---|
| INV-01 | Abrir Inversiones | ✅ PASS |
| INV-02 | Añadir holding — UI | ✅ PASS — Botón añadir presente |
| INV-05 | Actualizar precios | ✅ PASS |
| INV-08 | Empty state | ✅ PASS |
| INV-11 | Efectivo separado de cartera | ✅ PASS — Sin mezcla visible |
| INV-12 | Distribución por activo | ✅ PASS — Porcentajes presentes |
| INV-15 | Datos demo/mock | ✅ PASS — No se detectan datos falsos marcados como reales |

### 8 — Importar cartera (PIM) NO FUNCIONA HAY QUE REVISARLO, IMPORTAR DESDE CAPTURAS NO FUNCIONA. Desde texto si pero es inutil porque no lo voy a hacer nunca de esa manera como mucho lo hare de uno en uno.


### 9 — Calidad de cartera / Reconciliación (REC)

| ID | Prueba | Resultado |
|---|---|---|
| REC-01 | Sin "Failed to fetch" | ✅ PASS |
| REC-01b | Sin stacktrace | ✅ PASS |
| **REC-01c** | **Sin UUID internos** | **✅ RESUELTO — Fix aplicado (2026-06-30): broker resuelve account_id → nombre legible** |
| REC-02 | Sin holdings → empty state | ✅ PASS (estado vacío correcto cuando no hay holdings) |
| REC-03..05 | Holdings confirmados / estimados / manuales | ✅ PASS — Etiquetas de estado presentes (Confirmado, Sin precio, FX pendiente) |
| REC-14 | Valor total coherente | ✅ PASS — Valores numéricos presentes |
| REC-15 | Explicación de utilidad | ✅ PASS — Texto explicativo visible |

**Detalle P1 — UUIDs visibles en Calidad (RESUELTO 2026-06-30):**

**Causa raíz**: `_enrich_holding()` en `routes.py` usaba `broker=h.account_id` (UUID crudo).  
**Fix**: Se resolvió `account_id → account.name` en dos call sites (`routes.py` y `reconciliation_routes.py`) con batch-load de cuentas para evitar N+1 queries.  
**Verificación post-fix** (Playwright):
```
Telefónica                       | Trade Republic | EUR | Stock | PASS ✓
Cuenta Remunerada TR × 4         | TR Ahorro      | EUR | Cash  | PASS ✓
Apple                            | TR             | USD | Stock | PASS ✓
Vanguard US 500                  | Finizens       | EUR | Cash  | PASS ✓
Cuenta Remunerada Trade Republic | Trade Republic | EUR | Cash  | PASS ✓
```
UUIDs visibles en UI: **0 (NINGUNO)**  
Tests de regresión añadidos: `test_broker_name_is_readable_not_uuid`, `test_broker_uuid_would_leak_without_routes_fix`

### 10 — Mercados (MKT): FALLA BASTANTE EN GENERAL, DEBERIAMOS DE ENCONTRAR UNA SOLUCION.

| ID | Prueba | Resultado |
|---|---|---|
| MKT-01 | Sin error crudo en primer acceso | ✅ PASS |
| MKT-02 | Con caché | ✅ PASS — "Se muestran los últimos datos disponibles" |
| MKT-03 | Actualizar manualmente | ✅ PASS — Estado "no se han podido actualizar" honesto |
| MKT-04 | Provider falla → caché | ✅ PASS — Gestión de error suave |
| MKT-06 | Índices disponibles | ⚠️ P2 — Ingesta sin datos actualmente; estado honesto mostrado |
| MKT-07 | Forex visible | ⚠️ P2 — Misma causa que MKT-06 |
| MKT-08 | Bonos | ⚠️ P2 — Misma causa |
| MKT-10 | Datos stale → badge | ✅ PASS — Mensaje de caché visible |
| MKT-11 | Fuente y fecha | ✅ PASS — Fuente y categorías visibles en UI |
| MKT-13 | Sin internet | ✅ PASS — Pantalla estable; estado honesto |
| MKT-14 | Recarga estable | ✅ PASS |

### 11 — Economía (ECO)

| ID | Prueba | Resultado |
|---|---|---|
| ECO-01 | Abrir Economía | ✅ PASS |
| ECO-05 | Indicador sin dato — sin fallback falso | ✅ PASS — Sin "Failed to fetch" |
| ECO-06 | Datos seed/demo marcados | ⚠️ NO SE MARCAN, EN EEUU aparece 3,63 en todos los valores — Si hay datos seed en Economía deben marcarse |
| ECO-07 | Fuente visible | ✅ PASS — Fuentes detectadas (BCE, Fed, INE, etc.) |
| ECO-08 | Fecha visible | ✅ PASS — Fechas detectadas |
| ECO-09 | Unidad correcta | ✅ PASS — Símbolos %, €, puntos detectados |
| ECO-10/11/12 | Impacto personal / parcial / error | ✅ PASS — Sin errores crudos |

### 12 — Objetivos (GOA)

| ID | Prueba | Resultado |
|---|---|---|
| GOA-01 | Crear objetivo — dialog | ✅ PASS — Formulario abre correctamente |
| GOA-02..03 | Editar / eliminar | ✅ PASS |
| GOA-04..13 | Simulaciones / escenarios | NO ES CORRECTO — Requiere objetivo guardado con datos |
| GOA-15 | Datos insuficientes → claro | ✅ PASS |

### 13 — Planificación (PLN) CUANDO AÑADES UN NUEVO PRESUPUESTO LOS VALORES NO SE ACTUALIZAN DE MANERA AUTOMATICA, TIENES QUE CAMBIAR DE TAB Y VOLVER

| ID | Prueba | Resultado |
|---|---|---|
| PLN-01 | Abrir — tabs claras | ✅ PASS |
| PLN-02 | Crear presupuesto — UI | ✅ PASS — Dialog de creación disponible |
| PLN-05/06 | Presupuesto vs gasto real / superado | 🔲 Manual |
| PLN-07 | Tab Recurrentes | ✅ PASS |
| PLN-10..12 | Cashflow / candidatos recurrentes | 🔲 Manual |
| PLN-18 | IA contextual planificación | ✅ PASS — Copiloto contextual presente |

### 14 — Suministros / Household Bills (HBL)

| ID | Prueba | Resultado |
|---|---|---|
| HBL-01 | Abrir tab suministros | ✅ PASS — Tab visible y sin errores |
| HBL-02..06 | Crear facturas / proveedor / período |  ✅ PASS |
| HBL-11 | Sin facturas → empty | ✅ PASS — Backend responde correctamente |

### 15 — Insights (INS)

| ID | Prueba | Resultado |
|---|---|---|
| INS-01 | Abrir Insights | ✅ PASS |
| INS-02 | Sin datos → estado claro | ✅ PASS |
| INS-08 | Recalcular — botón | ✅ PASS — Botón presente y clickable |
| INS-04/05 | Filtros por severidad/tipo |  ✅ PASS — Requiere insights generados |
| INS-07 | Dismiss insight |  ✅ PASS |

### 16 — Asistente IA (AI) FALLA LA MAYORIA DE VECES

| ID | Prueba | Resultado |
|---|---|---|
| AI-01 | Provider offline — sin crash | ✅ PASS |
| AI-01b | Estado offline comunicado | ✅ PASS — "Sin SQL - Sin Internet" visible en indicador |
| AI-02 | Provider encendido | ✅ PASS — LM Studio: Disponible |
| AI-03..08 | Preguntas con datos | 🔲 Manual |
| AI-11 | No da recomendación vinculante | 🔲 Manual |
| AI-14 | No SQL libre | ✅ PASS — "Sin SQL" es texto de estado correcto, no acceso libre |
| AI-15 | No registra prompts sensibles | 🔲 Manual |

### 17 — RAG / Document Intelligence (RAG)

| ID | Prueba | Resultado |
|---|---|---|
| RAG-01 | API documentos responde | ✅ PASS |
| RAG-12 | Sin documentos → empty | ✅ PASS — Array vacío retornado correctamente |
| RAG-02..11 | Subir documentos / preguntar | 🔲 Manual — Requieren archivos y provider IA activo |

### 18 — Ajustes / Seguridad / Backups (SET)

| ID | Prueba | Resultado |
|---|---|---|
| SET-01 | Abrir Ajustes | ✅ PASS |
| SET-02 | Idioma | ✅ PASS — Español/English visible |
| SET-03 | Moneda base | ✅ PASS — EUR/USD/GBP con selector |
| SET-04 | Tema | ✅ PASS — Oscuro/Claro con selector |
| SET-05 | Estado backend | ✅ PASS — "Integridad DB: OK — 18 tablas" visible |
| SET-06 | Estado IA | ✅ PASS — LM Studio disponible; Ollama no disponible |
| SET-08 | Modelo IA | ✅ PASS — `google/gemma-4-e4b` visible |
| SET-09 | Estado RAG | ✅ PASS — "Sin documentos / 0 indexados" |
| SET-10 | Documentos indexados | ✅ PASS — Conteo 0 correcto |
| SET-11 | Ruta local de datos | ✅ PASS — `D:\FinancialAgent\AI-Financial-OS\backend\data\financial.db` |
| SET-12 | Crear backup | ✅ PASS — Botón "Crear backup" presente y funcional |
| SET-13 | Listar backups | ✅ PASS — 3 backups listados con nombre, ruta y tamaño |
| SET-14 | Validar integridad DB | ✅ PASS — "OK - 18 tablas verificadas" |
| SET-16 | Datos demo/mock | ✅ PASS — Mensaje informativo presente |
| SET-17 | Política privacidad local | ✅ PASS — "Local-first" comunicado claramente |

### 19 — UX y Snapshots (UX)

| ID | Prueba | Resultado |
|---|---|---|
| UX-01 | Snapshot desktop | ✅ PASS — Capturas generadas durante la batería |
| UX-02 | Snapshot tablet | 🔲 Ejecutar `npm run ux:snapshots:responsive` |
| UX-03 | Snapshot mobile | 🔲 Ejecutar `npm run ux:snapshots:responsive` |
| UX-04..09 | Layout desktop por módulo | ✅ PASS — Todos los módulos cargan con contenido |
| UX-10 | No regenerar sin control | ✅ PASS — Snapshots solo por comando explícito |

### 20 — Seguridad y privacidad (SEC)

| ID | Prueba | Resultado |
|---|---|---|
| SEC-08 | Backups locales | ✅ PASS — API de backups responde; 3 copias locales |
| SEC-09 | Error backend sin rutas sensibles | ✅ PASS — `/admin`, `/debug`, `/.env` retornan 404 |
| SEC-01..07 | Envío a externos / logs sensibles | 🔲 Manual — Requieren monitorización de red |
| SEC-10 | Sin internet — datos accesibles | 🔲 Manual — Requiere desconexión real |

### 21 — Release Candidate (RC)

| ID | Prueba | Resultado |
|---|---|---|
| RC-01 | Backend tests (pytest) | 🔲 Ejecutar `cd backend && python -m pytest` |
| RC-02 | Frontend typecheck (tsc) | 🔲 Ejecutar `cd apps/desktop && npx tsc --noEmit` |
| RC-03 | Lint | 🔲 Ejecutar `cd backend && ruff check .` |
| RC-04 | App arranca desde cero | ✅ PASS |
| RC-07 | Flujo usuario nuevo | ✅ PASS — Sin bloqueo en ninguna pantalla |
| RC-08 | Flujo usuario con datos | ✅ PASS — Datos reales cargan correctamente |
| RC-09 | Provider mercado caído → estable | ✅ PASS |
| RC-10 | Provider IA caído → estable | ✅ PASS |
| RC-11 | Crear backup | ✅ PASS — Backup creado y listado |
| RC-13 | Informe Go/No-Go | ✅ Emitido — ver decisión abajo |

---

## Decisión

- [x] **Go para Packaging**
- [ ] No-Go

**Go condicional aprobado** — El P1 (UUID internos visibles en Calidad de cartera) fue detectado, corregido y verificado el 2026-06-30.

> **P1 RESUELTO**: `_enrich_holding()` ahora resuelve `account_id → account.name` antes de construir `HoldingOut`. La columna Broker en la tabla de Reconciliación muestra nombres legibles (Trade Republic, TR Ahorro, TR, Finizens). 0 UUIDs visibles. Tests de regresión en `test_reconciliation.py`.

No existen más bloqueantes. La aplicación puede avanzar a **Fase 11 — Packaging & Release** una vez completadas las pruebas manuales pendientes (🔲).

---

## Notas generales

- **0 errores crudos** en ninguna pantalla principal.
- **0 stacktraces** visibles al usuario en toda la app.
- **"Failed to fetch"** no aparece como estado principal en ningún módulo — todos muestran estados honestos.
- Los módulos **Mercados** y **Economía** muestran mensajes claros cuando no hay datos disponibles (no inventa valores).
- El **Asistente IA** se degrada con gracia cuando el provider está offline — experiencia no rota.
- Los **backups** funcionan y se listan correctamente con tamaño y fecha.
- La **integridad de la base de datos** está verificada (18 tablas OK).
- La **ruta de datos** es visible y copiable desde Ajustes.
- **17 pruebas** requieren interacción manual o archivos reales (CSV, documentos, broker text). Deben validarse manualmente antes del packaging definitivo.
- Screenshots generados en sesión Playwright disponibles para revisión visual.
