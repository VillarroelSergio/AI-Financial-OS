# 31 — UX Flow Testing end-to-end con MCP chrome-devtools (ejecución autónoma por Claude Code)

## Objetivo

> Estado operativo vigente: consultar [`docs/testing/README.md`](testing/README.md).
> El runner actual usa datos temporales fuera del repositorio, en
> `%TEMP%\\ai-financial-os-e2e`, y los borra al terminar. Las secciones históricas
> de este documento se conservan como diseño de los FLOW; los comandos y el estado
> de implementación se mantienen en la guía operativa.

Dar a Claude Code un plan de pruebas de **flujo interactivo end-to-end de toda la
aplicación** que pueda ejecutar de forma autónoma usando un servidor MCP de tipo
`chrome-devtools` (navegación real, clicks, formularios, lectura de consola y de red),
sin intervención humana durante la ejecución.

Esto **no sustituye** `tools/ux-snapshot` (Playwright + mock data, capturas estáticas
por ruta, descrito en `13_CLAUDE_CODE_GUIDE.md`). Lo complementa:

| | `ux-snapshot` (existente) | Este plan (MCP chrome-devtools) |
|---|---|---|
| Naturaleza | Capturas estáticas por ruta | Flujo interactivo con acciones reales |
| Datos | Mock fixtures (`VITE_USE_MOCK_DATA=true`) | Backend real local (SQLite/DuckDB reales) |
| Qué valida | Que la pantalla renderiza sin romperse | Que las acciones del usuario producen el efecto correcto de extremo a extremo, incluyendo entre módulos |
| Errores de red/consola | No se inspeccionan | Se capturan y se reportan |
| Persistencia entre pasos | No aplica (cada ruta es independiente) | Sí: un movimiento creado en la Fase B debe verse reflejado en Resumen, Insights, Balance General, etc. |

## Alcance

**Todos los módulos de la aplicación**, en un único flujo continuo y ordenado que imita
el uso real: Resumen, Cuentas, Movimientos, Gastos, Facturas del hogar, Planificación
(presupuestos, recurrentes, cashflow), Inversiones, Objetivos, Mercados, Economía,
Insights, Patrimonio/Balance General (cierre de mes), Documentos/RAG, Asistente IA y
Ajustes. No queda ningún módulo fuera de esta ronda.

## Prerrequisitos técnicos

**Importante:** un MCP `chrome-devtools` controla pestañas de **Chrome**, no la ventana
nativa de Tauri. Por tanto las pruebas deben apuntar al frontend corriendo como app web
normal, no al binario empaquetado.

1. Backend arrancado en modo desarrollo:
   ```powershell
   cd backend
   uv run fastapi dev app/main.py
   ```
   Verificar `GET http://127.0.0.1:8010/health` → `{"status": "ok"}`.

2. Frontend en modo web (no `tauri dev`, no build empaquetado):
   ```powershell
   cd apps/desktop
   npm run dev
   ```
   Anotar el puerto real que reporta Vite (el mismo proyecto ya usa el 1422 para
   `ux-snapshot`; en `npm run dev` normal puede ser otro — Claude Code debe leer la
   salida de consola, no asumir un puerto fijo).

3. **Base de datos de prueba, no la de producción del usuario.** Antes de ejecutar,
   confirmar que `DATABASE_URL` / la ruta de datos apunta a un entorno de desarrollo
   (`data/financial.db` del repo, no `%APPDATA%\FinancialAgent\`). Si no hay forma de
   aislarlo con certeza, Claude Code debe **detenerse y preguntar** antes de crear datos
   de prueba — no debe arriesgarse a escribir sobre datos reales del usuario.

4. Estado de datos conocido al empezar: preferible partir de una base vacía o con datos
   demo claramente identificados, para que las aserciones "esto debe aparecer" no
   choquen con datos preexistentes ambiguos.

5. Conectividad opcional a proveedores de mercado/macro (internet real, no mockeada).
   Mercados y Economía consultan proveedores externos (Stooq, ECB, FRED, etc. — ver
   `15_MARKET_PROVIDERS.md`). Si el entorno de ejecución no tiene salida a internet,
   las fases G y H deben tratarse como pruebas de **estado degradado controlado**
   (partial/error visibles y honestos), no como fallo del plan.

6. IA local disponible (Ollama o LM Studio) para la Fase K. Si no está disponible,
   la Fase K se convierte en prueba de **healthcheck negativo controlado** (ver
   FLOW-28), no se omite sin más.

7. Herramientas MCP esperadas (nombres orientativos del `chrome-devtools-mcp`
   estándar; Claude Code debe adaptarlos al servidor realmente conectado):
   `navigate_page`, `take_snapshot`, `click`, `fill`, `fill_form`, `hover`, `wait_for`,
   `take_screenshot`, `list_console_messages`, `list_network_requests`,
   `evaluate_script`.

## Convenciones para cada caso de prueba

Cada caso sigue el formato:

```
ID: FLOW-XX
Módulo:
Precondición:
Pasos (acción MCP → resultado esperado):
Aserciones:
  - UI: qué debe verse
  - Red: qué llamada debe dispararse y con qué status
  - Consola: sin errores no controlados (excepciones no capturadas)
Captura: nombre de archivo de evidencia (take_screenshot)
```

Regla de consola: un `console.error` NO es automáticamente un fallo si corresponde a un
manejo de error controlado y visible en UI (p. ej. proveedor externo caído mostrando
estado `error`/`partial` en pantalla). Sí es un fallo si es una excepción de React no
capturada, una promesa rechazada sin manejar, o un log de stack trace.

Regla de red: cualquier respuesta `5xx` es fallo salvo que el caso la esté probando
explícitamente. Un `4xx` esperado (validación) no es fallo si la UI lo traduce en un
mensaje comprensible.

Regla de datos externos: para Mercados y Economía, un dato `stale`, `partial` o con
`quality_score` bajo **no es un fallo en sí mismo** — el contrato del proyecto exige
mostrar ese estado honestamente (`03_ARCHITECTURE.md`, Fase 6.4). El fallo es que la UI
lo presente como dato fresco/fiable cuando no lo es, o que contradiga su propio badge
(ver FLOW-20).

---

## Fase A — Arranque y fundamentos

### FLOW-01 — Arranque y estado inicial de Resumen

- Navegar a `/`.
- Esperar a que desaparezca cualquier estado de loading visible (mismo criterio que usa
  `ux-snapshot`: `[data-app-ready="true"]` si existe en la ruta).
- Aserciones:
  - Hero de patrimonio visible con valores numéricos coherentes (no `NaN`, no
    `undefined`, no placeholders vacíos si hay datos).
  - Si la base está vacía: empty state explícito, no un dashboard con ceros silenciosos
    que parezcan datos reales.
  - `GET /api/dashboard/overview` → 200.
  - Sin errores de consola no controlados.
- Guardar el patrimonio/liquidez mostrados como **snapshot de referencia T0** para
  comparar en fases posteriores.

### FLOW-02 — Crear una cuenta

- Ir a Cuentas.
- Crear cuenta: nombre `E2E Test Bank`, tipo `bank`, divisa `EUR`, saldo inicial `1000`.
- Aserciones:
  - `POST /api/accounts` → 201.
  - La cuenta aparece en el listado con el nombre exacto introducido, sin UUID visible
    (regla de `27_FINANCIAL_COMMAND_CENTER_UI_POLISH.md`).
  - El saldo mostrado coincide con el introducido.

---

## Fase B — Movimientos y Gastos

### FLOW-03 — Registrar movimientos

- Ir a Movimientos.
- Crear transacción de gasto: cuenta `E2E Test Bank`, categoría `Restaurante`, importe
  `-42.30`, fecha de hoy, descripción `E2E lunch test`.
- Crear transacción de ingreso: `+500`, categoría `Salario`.
- Aserciones:
  - `POST /api/transactions` → 201 en ambos casos.
  - Ambas filas visibles en el listado, con signo e importe correctos, sin UUID visible.
  - Filtro por cuenta/categoría/tipo funciona (probar al menos uno).

### FLOW-04 — Gastos: agregación y drilldown

- Ir a Gastos.
- Aserciones:
  - La categoría `Restaurante` refleja `42.30` en el periodo actual.
  - El porcentaje mostrado es `importe_categoria / gasto_total * 100` (verificar
    coherencia aritmética simple con el resto de categorías visibles, según
    `03_ARCHITECTURE.md` Fase 6.4).
  - Drilldown: click en la categoría abre detalle con el movimiento `E2E lunch test`
    listado (`GET /api/dashboard/spending/category-detail`, ver `02_ROADMAP.md`
    Fase 6.4.1).
  - Categorías pequeñas agrupadas en "Otros" si aplica (regla de
    `27_FINANCIAL_COMMAND_CENTER_UI_POLISH.md`).

### FLOW-05 — Verificación cruzada en Resumen

- Volver a Resumen.
- Aserciones:
  - El patrimonio/liquidez ha cambiado respecto al snapshot T0 (FLOW-01) en la
    dirección esperada (+500 −42.30 +1000 de la cuenta nueva, de forma aproximada, no
    exacta al céntimo si hay redondeos).
  - Sin error 5xx en `GET /api/dashboard/overview`.

---

## Fase C — Facturas del hogar

### FLOW-06 — Alta de factura

- Ir a Facturas del hogar (household bills).
- Crear factura: proveedor `E2E Iberdrola`, tipo `electricity`, periodo del mes actual,
  importe `95.00`, recurrente = sí.
- Aserciones:
  - `POST /api/household-bills` → 201.
  - Aparece en el listado con proveedor y tipo correctos.

### FLOW-07 — Resumen de facturas

- Ir a la vista de resumen de facturas.
- Crear una segunda factura del mismo proveedor/tipo con importe `140.00` (subida
  >20%) para forzar el caso de anomalía.
- Aserciones:
  - `GET /api/household-bills/summary` → 200.
  - El proveedor `E2E Iberdrola` aparece agrupado, con `change_pct` calculado y
    `anomaly: true` cuando la subida supera el 20%, según
    `04_DATA_MODEL.md`/`11_API_CONTRACT.md`.
  - `next_estimate` no vacío.

---

## Fase D — Planificación (presupuestos, recurrentes, cashflow)

### FLOW-08 — Crear presupuesto

- Ir a Planificación → Presupuestos.
- Crear presupuesto para categoría `Restaurante`, importe `500`, `alert_threshold_pct`
  `80`.
- Aserciones:
  - `POST /api/budgets` → 201.
  - Aparece la tarjeta de presupuesto.

### FLOW-09 — Comparativa presupuesto vs gasto real

- Aserciones:
  - `GET /api/budgets/comparison?month=YYYY-MM` → 200.
  - El gasto real de `Restaurante` (42.30€ de FLOW-03) se refleja en `actual_amount`,
    con `consumption_pct` coherente (`42.30/500 ≈ 8.5%`) y `alert: false` (por debajo
    del umbral del 80%).

### FLOW-10 — Recurrentes: candidatos detectados

- Ir a Planificación → Recurrentes.
- Si el histórico de movimientos de prueba no genera candidatos de forma natural (se
  requieren varias ocurrencias similares), documentar como `BLOCKED` con motivo en vez
  de forzar datos artificiales que distorsionen otras fases. Si existen datos previos
  suficientes, continuar.
- Aserciones (si hay candidatos):
  - `GET /api/recurring/candidates` → 200.
  - Cada candidato muestra nombre, importe/rango, frecuencia, próxima fecha,
    confianza y evidencia, según `23_BUDGETS_RECURRING_CASHFLOW.md`.

### FLOW-11 — Alta manual de recurrente y calendario

- Crear recurrente manualmente: nombre `Netflix E2E`, importe `15.99`, tipo `expense`,
  frecuencia `monthly`, día `8`.
- Aserciones:
  - `POST /api/recurring` → 201.
  - `GET /api/recurring/calendar?days=60` → 200, incluye una ocurrencia de
    `Netflix E2E` en los próximos 60 días.

### FLOW-12 — Previsión de cashflow

- Ir a la pestaña Cashflow.
- Aserciones:
  - `GET /api/cashflow/forecast?months=3` → 200.
  - `projected_expenses` del primer mes incluye al menos el recurrente creado
    (`recurring_expenses >= 15.99`).
  - El gráfico de barras se renderiza.

---

## Fase E — Inversiones

### FLOW-13 — Importar cartera (entrada rápida manual)

- Ir a Inversiones → "Importar cartera" → "Entrada rápida" (evitar dependencia de OCR,
  fuera de alcance según `20_PORTFOLIO_IMPORT_ASSISTANT.md` Fase 10.5).
- Introducir un holding manual sencillo (ticker con cobertura conocida, o marcado
  explícitamente `manual` si no hay red de mercado disponible).
- Pasar por la tabla editable de revisión **sin confirmar aún**.
- Aserciones:
  - El estado de importación mostrado (`READY` / `MANUAL` / `REVIEW`, etc.) es
    coherente con los datos introducidos.
  - **No** se ha creado ningún holding todavía (no debe haber `POST
    /api/investments/import/confirm` disparado antes del click de confirmar
    explícito) — principio de "asistida, no automática".
- Confirmar importación.
- Aserciones tras confirmar:
  - `POST /api/investments/import/confirm` → 200/201, `created >= 1`.
  - El holding aparece en el listado de Inversiones.

### FLOW-14 — Reconciliación de cartera

- Ir a la pestaña de Calidad de cartera / Reconciliación.
- Aserciones:
  - `GET /api/investments/reconciliation` → 200.
  - El holding de FLOW-13 aparece con uno de los seis `quality_state` definidos en
    `22_PORTFOLIO_RECONCILIATION_ANALYTICS.md` (no vacío ni `undefined`).
  - Los porcentajes de completitud suman ~100%.
  - Si hay concentración de un único activo/divisa >umbral, aparece la alerta
    correspondiente.

### FLOW-15 — Fondo con valoración manual o cuenta remunerada (INV-3/INV-4)

- Elegir uno de los dos caminos según lo que exponga la UI:
  - **Fondo:** alta de fondo (`POST /api/investments/funds`) + registrar un snapshot de
    valor (`POST /api/investments/funds/{holding_id}/snapshots`).
  - **Cuenta remunerada:** alta de cuenta remunerada (`POST /api/investments/savings`)
    y comprobar la proyección de intereses
    (`GET /api/investments/savings/{account_id}/projection`).
- Aserciones:
  - La operación elegida responde 200/201.
  - Si es fondo: el gráfico de evolución de valor se actualiza tras el snapshot.
  - Si es cuenta remunerada: la proyección devuelve una serie mensual con
    `total_interest` no nulo, usando el tipo BCE cacheado
    (`GET /api/market-intelligence/rates/ecb-deposit-facility`) o modo `estimated` si
    no hay ingesta previa.

---

## Fase F — Objetivos

### FLOW-16 — Crear objetivo y simular escenarios

- Ir a Objetivos.
- Crear objetivo: nombre `E2E Fondo Test`, tipo `savings`, importe objetivo `10000`,
  importe actual `2000`, aportación mensual `300`.
- Abrir el panel "Proyección y escenarios".
- Mover el slider de inflación si el MCP permite `drag`; si no, verificar solo que el
  control existe y usar el valor por defecto.
- Aserciones:
  - `POST /api/goals` → 201.
  - `POST /api/goals/{id}/simulate` → 200, `scenarios` de longitud 3
    (conservador/base/optimista), según `21_GOALS_SIMULATIONS.md`.
  - El gráfico de área se renderiza (contenedor SVG/canvas de recharts presente).
  - Las tres tarjetas de escenario muestran fecha estimada o "No alcanzable", nunca un
    valor vacío.
  - `GET /api/goals/{id}/progress` → 200, `progress_pct` coherente
    (`2000/10000 = 20%`).

---

## Fase G — Mercados

### FLOW-17 — Snapshot de mercados

- Ir a Mercados.
- Aserciones:
  - `GET /api/market-intelligence/snapshot/market` → 200 (o error controlado si no hay
    red — ver prerrequisito 5).
  - Secciones índices/cripto/commodities muestran `provider_id` y `quality_score`
    visibles, no solo el valor numérico.
  - `DataStatusBadge` por fila coherente con la frescura real del dato.

### FLOW-18 — Divisas (comprobación del defecto histórico EUR/USD)

- Ir a la pestaña Divisas.
- Aserciones:
  - `GET /api/market-intelligence/snapshot/forex` → 200.
  - Ningún par de divisas distinto de EUR/USD muestra el mismo valor que EUR/USD
    (regresión directa del defecto MKT-1 documentado en memoria de proyecto —
    contaminación de todas las filas de Divisas). Si se reproduce, es un **fallo
    crítico a reportar**, no una nota menor.

### FLOW-19 — Bonos

- Ir a la pestaña Bonos.
- Aserciones:
  - `GET /api/market-intelligence/snapshot/bonds` → 200.
  - La tabla de bonos **no está vacía** si el proveedor de curva respondió con éxito
    (regresión del defecto "tab de Bonos vacío"). Si el proveedor real falló (sin red),
    debe mostrarse un estado vacío/error honesto, no confundirse con el bug.
  - Cada maturity mostrada coincide con la codificada (`us_2y` → `2Y`, etc.), según
    `15_MARKET_PROVIDERS.md`.

### FLOW-20 — Coherencia del badge global de calidad

- Aserciones:
  - El badge de calidad global de Mercados no contradice el detalle por fila (p. ej.
    badge "actualizado" cuando alguna fila individual está `stale`/`error`) —
    regresión del defecto "badge de calidad global contradictorio".
  - `GET /api/market-intelligence/ingest-status` → 200, `storage: "file"` (no
    `"memory"` — regresión de la fragilidad mono-escritor de DuckDB ya migrada a
    SQLite WAL, ECO-3b).

---

## Fase H — Economía

### FLOW-21 — Snapshot macro

- Ir a Economía.
- Aserciones:
  - `GET /api/market-intelligence/snapshot/macro` → 200 (o error controlado si no hay
    red).
  - Cada indicador muestra `unit` según catálogo (no la unidad cruda del proveedor),
    `previous_value`/`delta` cuando existan, y sparkline (`history`) si hay al menos 2
    puntos.
  - Sin datos repetidos por fallback silencioso entre regiones (regla de
    `02_ROADMAP.md` Fase 10.5).

### FLOW-22 — Impacto personal

- Aserciones:
  - `GET /api/market-intelligence/personal-impact` → 200.
  - Las comparativas que no aplican al perfil de prueba (sin deuda, sin cartera con
    exposición relevante, etc.) están **ausentes** de la respuesta, no presentes con
    `signal: "no_data"` genérico salvo que falte específicamente el dato de mercado
    (regla exacta de `11_API_CONTRACT.md`).
  - Ninguna comparativa afirma un veredicto (`signal_text`) cuando `signal: "no_data"`.

---

## Fase I — Insights

### FLOW-23 — Listado de insights

- Ir a Insights (o el panel donde se expongan).
- Aserciones:
  - `GET /api/insights` → 200.
  - Con los movimientos/presupuestos creados en fases previas, debería aparecer al
    menos un insight de tipo `spending_anomaly`, `monthly_comparison`,
    `savings_rate`, `cashflow_alert` o `budget_alert` — si no aparece ninguno,
    verificar `data_status` en la respuesta antes de marcarlo como fallo (podría ser
    `insufficient` legítimamente con solo 1-2 movimientos de prueba).
  - Badge de estado (`complete`/`partial`/`insufficient`/`empty`/`error`) coherente
    con el cuerpo mostrado — no pueden contradecirse (regla de
    `16_INSIGHTS_ENGINE.md`).

### FLOW-24 — Descartar y restaurar un insight

- Descartar (`dismiss`) un insight visible.
- Aserciones:
  - `POST /api/insights/{id}/dismiss` → 200, el insight desaparece del listado activo.
  - `POST /api/insights/{id}/restore` → 200, el insight reaparece (undo, INS-7).

---

## Fase J — Patrimonio / Balance General (cierre de mes asistido)

### FLOW-25 — Checklist de preparación del cierre

- Ir a Resumen → Balance General.
- Aserciones:
  - `GET /api/net-worth/snapshot-readiness?month=YYYY-MM` → 200.
  - `items[]` muestra checklist con `status: ok|stale|missing` y `cta_route` cuando
    falte algo — nunca un `ready: true` si hay ítems `missing`.

### FLOW-26 — Crear snapshot de patrimonio

- Ejecutar el cierre de mes asistido desde la UI (nunca debe ocurrir automáticamente
  sin esta acción explícita, según `16_INSIGHTS_ENGINE.md` D7).
- Aserciones:
  - `POST /api/net-worth/snapshots` → 201, o `409` si `force_partial=false` y faltan
    elementos (verificar que la UI ofrece la opción de `force_partial` en ese caso).
  - `GET /api/net-worth/balance-sheet?month=YYYY-MM` → 200, `net_worth = total_assets
    − total_liabilities` es aritméticamente correcto con los datos visibles.
  - Repetir la creación del snapshot para el mismo mes es idempotente (DELETE+INSERT,
    no duplica filas).

---

## Fase K — Documentos / RAG

### FLOW-27 — Subir documento y consultar

- Ir a Documentos.
- Subir un documento de texto simple (`.txt` o `.md`) con contenido conocido (p. ej.
  una nota que mencione una fecha de vencimiento concreta).
- Aserciones:
  - `POST /api/rag/documents/upload` → 200/201.
  - El documento aparece en `GET /api/rag/documents`.
- Preguntar en el buscador RAG algo cuya respuesta esté literalmente en el documento
  subido.
- Aserciones:
  - `POST /api/rag/query` → 200, la respuesta incluye `sources` trazables al
    documento y fragmento subidos (no una respuesta genérica sin fuente).

---

## Fase L — Asistente IA

### FLOW-28 — Healthcheck del provider

- Ir al Asistente IA.
- Aserciones:
  - `GET /api/ai/health` → 200 con el estado real del provider configurado.
  - Si el provider local (Ollama/LM Studio) no está disponible en el entorno de
    ejecución, la UI debe mostrar un estado `503`/error honesto, no una carga
    infinita (regresión de P0-05, Fase 10.6). En ese caso, marcar FLOW-29 como
    `BLOCKED` con este motivo y continuar con el resto del plan.

### FLOW-29 — Chat contextual con tool call

- Desde un módulo con datos (p. ej. Gastos, tras FLOW-03/04), abrir el copiloto
  contextual y preguntar algo que requiera una tool determinista (p. ej. "¿cuánto he
  gastado en Restaurante este mes?").
- Aserciones:
  - `POST /api/ai/chat` → 200, con `tool_calls` no vacío.
  - La cifra citada en la respuesta coincide con el dato real mostrado en la propia
    pantalla de Gastos (42.30€ del movimiento de prueba) — la IA no debe inventar un
    número distinto al de la tool.
  - El contexto enviado solo incluye las claves permitidas (`module`, `route`,
    `period`, `visible_metrics`, `data_status`, `selected_entity`,
    `suggested_action`), verificable inspeccionando el payload de la petición con
    `list_network_requests`.
  - Sin recomendaciones vinculantes de compra/venta de activos en el texto de
    respuesta (guardrail de `06_AI_STRATEGY.md`).

---

## Fase M — Ajustes

### FLOW-30 — Estado de seguridad e integridad

- Ir a Ajustes.
- Aserciones:
  - `GET /api/security/status` → 200, muestra ruta local de base de datos y política
    de datos demo.
  - `GET /api/security/integrity` → 200, `PRAGMA integrity_check` correcto y número de
    tablas verificadas visible en UI.

### FLOW-31 — Backup manual desde UI

- Pulsar "Crear backup" en Ajustes.
- Aserciones:
  - `POST /api/security/backups` → 200/201.
  - `GET /api/security/backups` → 200, el nuevo backup aparece en el listado con fecha
    y tamaño.
  - El contador de backups disponibles en la UI se actualiza sin recargar la página
    manualmente.

---

## Fase N — Cierre y limpieza

### FLOW-32 — Consistencia final en Resumen

- Volver a Resumen.
- Aserciones:
  - El patrimonio total ha evolucionado de forma consistente con la suma de todas las
    operaciones de las fases anteriores respecto al snapshot T0 (FLOW-01) — no se
    exige un cálculo exacto en el test, basta con verificar la dirección y orden de
    magnitud esperados.
  - Ningún error de consola acumulado a lo largo de toda la sesión de navegación
    completa (todas las fases).

### FLOW-33 — Limpieza (si el entorno de prueba lo permite)

- Eliminar, en orden inverso a su creación: snapshot de patrimonio del mes de prueba
  (si el endpoint lo permite), objetivo, holding(s) de inversión, recurrente,
  presupuesto, facturas, transacciones, cuenta.
- Aserciones:
  - Cada `DELETE` responde con el código esperado (204 en la mayoría, según
    `11_API_CONTRACT.md`).
  - Resumen refleja el patrimonio de vuelta a un estado equivalente al snapshot T0.
- Si el entorno de prueba es efímero (base de datos descartable), este paso es
  opcional pero recomendado para dejar el flujo repetible.

---

## Qué debe entregar Claude Code al terminar

Un informe con:

1. Tabla resumen `FLOW-01`…`FLOW-33`: PASS / FAIL / BLOCKED, con una línea de motivo si
   no es PASS. Agrupar por fase (A–N) para lectura rápida.
2. Capturas de pantalla (`take_screenshot`) de cada paso relevante, especialmente los
   fallos.
3. Lista de errores de consola y llamadas de red fallidas encontradas, aunque no hayan
   hecho fallar el caso — candidato a añadir a la tabla de `TD-XX` en `02_ROADMAP.md`.
4. Cualquier discrepancia entre el comportamiento observado y lo documentado en los
   ficheros de spec citados en cada caso — señal de que la documentación o el código se
   desviaron.
5. Atención especial y explícita a los tres defectos de regresión marcados en la Fase G
   (FLOW-18, FLOW-19, FLOW-20): confirmar si siguen reproduciéndose o si MKT-1/MKT-2
   ya los resolvió.

## Criterios de éxito de esta tarea

- Los 33 casos ejecutados sin intervención humana (salvo los `BLOCKED` documentados por
  falta de red o de provider IA local, que son aceptables si están justificados).
- Ningún dato de producción real tocado (verificación del prerrequisito 3 antes de
  empezar es bloqueante, no opcional).
- Informe entregado en formato consistente con el resto de artefactos del proyecto.
- Cualquier hallazgo de bug real (no de entorno) documentado con pasos de
  reproducción, no solo mencionado de pasada.

---

## Piloto implementado: FLOW-01 a FLOW-05

El primer piloto está implementado en `tools/ux-snapshot/run-flow-01-05.ts` y se
puede ejecutar desde `tools/ux-snapshot/`:

```powershell
npm run e2e:flow-01-05
npm run e2e:flow-01-05:headed
```

En modo `headed`, el runner ralentiza las acciones y escribe los campos de texto
carácter a carácter. La velocidad se puede ajustar con
`E2E_ACTION_DELAY_MS` y `E2E_TYPE_DELAY_MS`, por ejemplo:

```powershell
$env:E2E_ACTION_DELAY_MS = "1200"
$env:E2E_TYPE_DELAY_MS = "80"
npm run e2e:flow-01-05:headed
```

El runner arranca el backend y el frontend web fuera de Tauri, usa una base
SQLite/DuckDB temporal bajo `.e2e-data/`, aborta si los puertos de prueba están
ocupados, comprueba que `/api/accounts` está vacío y guarda capturas e informe en
`ux-snapshots/e2e/flow-01-05/`. También registra errores de consola y respuestas
HTTP 5xx.

### Resultado del piloto

## Segunda tanda implementada: FLOW-06 a FLOW-33

Ejecutar desde `tools/ux-snapshot/`:

```powershell
npm run e2e:flow-01-33
npm run e2e:flow-01-33:headed
```

La ejecución valida de forma determinista FLOW-06â€¦12, FLOW-16,
FLOW-23â€¦26 y FLOW-30â€¦33 sobre la misma base efímera. FLOW-10 se marca
`BLOCKED` cuando no existen suficientes ocurrencias históricas. Los flujos de
mercados, inversiones, RAG e IA (FLOW-13â€¦15, 17â€¦22 y 27â€¦29) quedan
`BLOCKED` hasta disponer de fixtures/providers externos.

La última ejecución produjo PASS en todos los flujos deterministas salvo
FLOW-09. Ese caso detecta una discrepancia real: `/api/budgets/comparison`
devuelve el gasto de Restaurante como importe negativo, mientras el contrato
del flujo exige `42,30` positivo y un consumo aproximado del `8,5%`. El informe
completo queda en `ux-snapshots/e2e/flow-01-05/report.md` y el runner sale con
código distinto de cero mientras esa regresión permanezca.

FLOW-01…FLOW-05 pasan sin errores de consola ni respuestas HTTP 5xx.

El criterio original de FLOW-05 necesitaba corregirse: actualmente
`GET /api/dashboard/overview` calcula `net_worth` desde los saldos de cuentas y la
cartera. Los movimientos alimentan `monthly_income` y `monthly_expense`, pero no
modifican automáticamente `Account.current_balance`. Por eso el piloto verifica:

- patrimonio: `+1000 €` por el saldo inicial de la cuenta;
- ingresos mensuales: `+500 €`;
- gasto mensual: `42,30 €`.

Si el producto debe reflejar también los movimientos en el patrimonio, primero hay
que definir e implementar esa regla de dominio y después restaurar la aserción de
`+1457,70 €`.
