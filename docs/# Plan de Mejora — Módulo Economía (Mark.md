# Plan de Mejora — Módulo Economía (Market Intelligence)

**Fecha:** 2026-07-06
**Estado:** Borrador para revisión
**Base:** Análisis end-to-end del flujo catálogo → ingesta → almacenamiento → API → UI
**Docs de referencia:** `03_ARCHITECTURE.md`, `07_ECONOMIC_INTELLIGENCE.md`, `15_MARKET_PROVIDERS.md`, `26_UX...md` §10.5.3, `PRE_RELEASE_AUDIT.md` (BE-2, BE-6), `12_DEVELOPMENT_WORKFLOW.md`

---

## Diagnóstico consolidado

| # | Problema | Severidad | Naturaleza |
|---|----------|-----------|------------|
| P1 | Contrato laxo de adapters: `fetch()` ignora el indicador pedido (Eurostat), `supports()` permisivo por defecto → contaminación de datos ("indicadores clonados") mitigada con 3 capas defensivas que no cierran el bug de raíz | **Crítica** | Diseño |
| P2 | Catálogo declara cobertura que la ingesta no cumple: INE solo implementa `ipc_general` pero es primario de 6 indicadores; PMIs de España sin proveedor posible (entradas muertas) | **Alta** | Datos/honestidad |
| P3 | Tests de `market_intelligence` fuera del ciclo pytest (audit BE-2) + sin `conftest.py` (BE-6): cualquier refactor es a ciegas | **Alta** | Proceso |
| P4 | Endpoint tipos BCE hace ingesta síncrona dentro del GET — viola la regla "leer nunca ingesta"; además duplica almacén con `ReferenceRateObservation` (SQLite) | **Alta** | Regla arquitectónica |
| P5 | DuckDB mono-escritor: fallback silencioso a BD en memoria + maquinaria de warnings; fragilidad operativa principal | **Alta** | Arquitectura (requiere ADR) |
| P6 | Lecturas macro duplicadas (`impact.py` vs `personal_economy.py`), SQL crudo saltándose el repository, periodos malformados en escritura | **Media** | Deuda |
| P7 | `impact.py`: 578 líneas, 11 comparativas hardcodeadas, umbrales mágicos, `portfolio_return` con media simple no ponderada | **Media** | Deuda + corrección de sesgo |
| P8 | Cadencia única de 6h ignora `frequency` del catálogo; `historical`/`retention` son metadatos muertos; `is_available()` hace HEAD redundante | **Media** | Eficiencia |
| P9 | Frontend: hook manual reimplementando react-query, 5 requests paralelos + polling, agrupado temático acoplado a ids de catálogo en la UI | **Baja** | Deuda |

**Qué se conserva (explícitamente):** API que solo lee de almacén (nunca providers en caliente), degradación elegante con `_safe()` y `no_data`, catálogo YAML como fuente de verdad, `quality_score` por observación propagado a UI, cruce determinista macro↔personal sin LLM.

---

## Principios del plan

1. **Tests antes que refactor.** No se toca el contrato de adapters sin red de seguridad (P3 primero).
2. **Raíz antes que síntoma.** El contrato estricto (P1) elimina las 3 capas defensivas; no se añaden más parches.
3. **Honestidad del catálogo antes que UI.** Un indicador que nunca tendrá datos no debe existir en el catálogo (coherente con "data integrity before UI").
4. **Cambios de almacén vía ADR, no de facto.** P5 contradice reglas vigentes de `03_ARCHITECTURE.md`; se decide con spike documentado.
5. **Sprints pequeños y secuenciales** con Definition of Done, según `12_DEVELOPMENT_WORKFLOW.md`.

---

## Sprints

### ECO-0 — Red de seguridad de tests *(prerequisito, ~0.5 día)*

Resuelve P3 (audit BE-2 + BE-6). Sin esto, todo lo demás es refactor a ciegas.

**Tareas:**
1. Mover `backend/tests/market_intelligence/` a `backend/app/modules/market_intelligence/tests/` **o** añadir `"tests"` a `testpaths` en `pyproject.toml` (decidir según convención del resto de módulos; preferencia: co-locar con el módulo).
2. Crear `conftest.py` con fixtures: DuckDB in-memory, `CatalogLoader` mockeado, adapters fake.
3. Ejecutar la suite completa, catalogar tests rotos por obsolescencia vs. por bug real. Arreglar u marcar `skip` con razón explícita.
4. Añadir test de caracterización del comportamiento actual del orquestador (cadena primary→secondary→fallback) que sirva de base para ECO-1.

**DoD:** `uv run pytest` ejecuta los 13 ficheros en el ciclo estándar; 0 tests silenciosamente excluidos; CI verde o skips justificados.

---

### ECO-1 — Contrato estricto de adapters *(núcleo del plan, ~2-3 días)*

Resuelve P1. Es el cambio que más código elimina y más bugs cierra.

**Contrato nuevo (breaking, interno):**
- `fetch(catalog_item_id: str) -> AdapterResult` obligatorio en `BaseAdapter`. Se elimina la tolerancia `except TypeError` del orquestador (`orchestrator.py:68-71`).
- El `AdapterResult` devuelto debe contener **solo** datos del `catalog_item_id` pedido. El orquestador valida `result.catalog_item_id == requested_id` y descarta con log de health si no coincide.
- `supported_indicators` obligatorio (allowlist explícita). `supports()` sin declaración → `NotImplementedError`, no `True`.

**Tareas:**
1. Migrar los ~35 adapters al contrato nuevo. Los multi-indicador (Eurostat, OECD, World Bank) pasan a mapear `catalog_item_id → serie concreta de su API` y a declarar allowlist real.
2. Actualizar catálogo YAML: donde un secondary/fallback no soporte el indicador (según allowlist), eliminarlo de la cadena (el orquestador ya no lo intentará, pero el YAML debe reflejar la realidad).
3. **Borrar las 3 capas defensivas** una vez verde: `purge_mismatched_macro_observations()`, guard `_record_matches_catalog()`, detección de valores repetidos en lectura (`service.py:84-129`).
4. Purga única de datos contaminados existentes en DuckDB (script one-shot, con backup previo del fichero `.duckdb`).
5. Tests: por adapter (allowlist respetada, id correcto en resultado) y de orquestador (rechazo de resultado con id incorrecto).

**Riesgo y mitigación:** al eliminar la detección de repetidos en lectura, cualquier contaminación residual se haría visible en UI. Mitigación: la purga del paso 4 + un test de integración que verifique que no hay 3+ indicadores con mismo valor/periodo tras re-ingesta.

**DoD:** ningún adapter acepta indicadores fuera de su allowlist; las 3 capas defensivas eliminadas; suite ECO-0 + nuevos tests en verde; datos re-ingestados sin clones.

---

### ECO-2 — Auditoría y saneamiento del catálogo *(~1-2 días)*

Resuelve P2. Depende de ECO-1 (las allowlists hacen la auditoría mecánica).

**Tareas:**
1. Generar matriz indicador × proveedor: declarado en YAML vs. realmente soportado (derivable de las allowlists de ECO-1). Guardar como artefacto en `docs/internal/`.
2. **Eliminar entradas muertas:** `pmi_manufacturero_spain`, `pmi_servicios_spain` (S&P Global, de pago — no habrá proveedor). Alternativa si se quieren conservar: estado `disabled: true` en YAML con `reason`, que la ingesta ignore y la UI no arrastre como hueco.
3. **Cerrar el gap INE:** implementar en `ine.py` los indicadores donde INE es primario declarado y publica dato (paro EPA, PIB CNTR, producción industrial, IPC subyacente vía Tempus/API JSON del INE) **o** rebajar el primario declarado al proveedor que realmente sirve el dato (Eurostat con serie específica de España — ahora ya legal gracias al contrato de ECO-1, que exige serie ES, no EA20).
4. Verificar cobertura contra los "indicadores mínimos esperados" de la spec 10.5.3 (España/Eurozona/EEUU): cada uno debe tener al menos un proveedor real en su cadena.
5. Decisión sobre metadatos muertos `historical:`/`retention:`: eliminarlos del YAML (recomendado ahora) o dejarlos documentados como "reserved" hasta ECO-4/ECO-5. No dejarlos ambiguos.

**DoD:** 100% de los items del catálogo tienen ≥1 proveedor con soporte real verificado; 0 entradas que estructuralmente nunca tendrán datos; matriz de cobertura archivada; indicadores mínimos de 10.5.3 cubiertos o su ausencia justificada por escrito.

---

### ECO-3 — Corrección de reglas + spike de almacenamiento *(~2 días, incluye ADR)*

Resuelve P4 y decide P5.

**Parte A — Correcciones obligatorias (no requieren decisión):**
1. Eliminar la ingesta síncrona dentro del GET de tipos BCE (`routes.py:39-71`). El endpoint pasa a leer solo; si no hay dato, devuelve `no_data` y la ingesta programada lo rellenará. Restaura la regla "leer nunca ingesta" en el 100% de la API.
2. Unificar los dos almacenes de tipos BCE: una sola fuente de verdad (propuesta: `tipo_bce` en el almacén de Market Intelligence como serie macro; `ReferenceRateObservation` del módulo de inversiones pasa a leerla vía el módulo de lectura macro de ECO-4, o se documenta la separación con contrato explícito si el acoplamiento entre módulos no compensa).
3. Normalizar `period` a `YYYY-MM` / `YYYY-Qn` / `YYYY` **en escritura** (validador en el repository), eliminando los regex defensivos en lectura. Script de normalización de datos existentes.

**Parte B — Spike + ADR: ¿SQLite WAL o DuckDB?**

No se migra nada en este sprint; se decide con evidencia. El ADR (formato `engineering:architecture`) debe evaluar:

| Criterio | DuckDB (statu quo) | SQLite WAL |
|---|---|---|
| Mono-escritor / fallback a memoria | Fuente de fragilidad actual | Eliminado (WAL multi-lector, un escritor con busy_timeout) |
| Volumen real | 72 indicadores, filas/día ≈ decenas — ventaja columnar irrelevante | Sobrado |
| Maquinaria de warnings (`is_in_memory`, banners) | Necesaria | Se borra |
| Coste de migración | 0 | Repository + DDL `mi_*` + queries `QUALIFY ROW_NUMBER()` → CTEs; docs 03/15 |
| Uso analítico futuro (datasheets IA, agregaciones) | Punto fuerte declarado en `03_ARCHITECTURE.md` | Suficiente para el volumen actual; reevaluable |
| Dos motores en la app | Sí (SQLite personal + DuckDB MI) | Uno solo |

Resultado del spike: prototipo del repository sobre SQLite WAL con las 3-4 queries más complejas portadas + benchmark trivial. Con eso, decisión documentada. Si se decide migrar, la migración es un sprint propio (**ECO-3b**, ~2 días: DDL, port de queries, script de migración de datos, borrado de la maquinaria de warnings, actualización de `03_ARCHITECTURE.md` y `15_MARKET_PROVIDERS.md`). Si se decide conservar DuckDB, la alternativa mínima es garantizar proceso único por diseño (lockfile con mensaje claro al arrancar segundo backend) y documentarlo.

**DoD Parte A:** ningún GET ingesta; un solo almacén (o contrato documentado) para tipos BCE; `period` validado en escritura y datos históricos normalizados.
**DoD Parte B:** ADR aprobado con decisión y consecuencias; si migración, ECO-3b planificado.

---

### ECO-4 — Unificación de lecturas macro y refactor de impacto personal *(~2 días)*

Resuelve P6 y P7. Depende de ECO-3 (almacén decidido, periodos normalizados).

**Tareas:**
1. Crear módulo único `macro_series` (lectura): `latest(indicator_id)`, `value_year_ago(indicator_id)`, `change_12m(indicator_id)`. Sustituye `_macro_year_ago` (impact.py) y `_latest_and_year_ago` (personal_economy.py). Todo acceso vía repository — se elimina el SQL crudo de `impact.py:148-230`.
2. Refactor de `impact.py` a tabla de definiciones de comparativas: `{id, indicador_macro, métrica_personal, umbral_warning, umbral_alert, dirección, textos}`. Umbrales fuera del código (constantes en `constants.py` del módulo, siguiendo el patrón de Insights Engine). Las 11 comparativas actuales migran a datos; añadir una comparativa nueva = añadir una fila.
3. **Corregir `portfolio_return` a media ponderada por valor de posición** (`impact.py:72-80`). Es corrección de sesgo, no estilo: sin aritmética float en el cálculo (Decimal, según regla del proyecto). Test con cartera asimétrica (100€ vs 50.000€).
4. Endurecer matching de categorías: sustituir subcadenas ("alimentaci", "casa") por mapeo explícito a `category_id`/slug del modelo de categorías, con fallback documentado. Ídem para matching de noticias (el caso `"ipc" in "participación"` debe tener test de regresión).

**DoD:** una sola implementación de lectura macro consumida por service/impact/personal_economy; `impact.py` reducido a ~1/3; retorno ponderado con test; matching sin falsos positivos conocidos.

---

### ECO-5 — Scheduler por frecuencia e higiene de ingesta *(~1-2 días)*

Resuelve P8.

**Tareas:**
1. Scheduler que respeta `frequency` del catálogo: diario (Euríbor, forex, índices), mensual (IPC, paro), trimestral (PIB). Implementación simple: en cada tick (p. ej. cada hora), ingestar solo items cuyo `last_success + frequency` haya vencido. Sin dependencias nuevas si `asyncio`/thread actual basta.
2. Eliminar el HEAD redundante de `is_available()` en el camino caliente: el propio `fetch` con timeout y el health log ya cubren la detección de caída. `is_available()` queda para diagnóstico manual/CLI.
3. Estado de ingesta estructurado: `run_id`, progreso por indicador, resultado por item (ok/fallback_used/failed), protegido con lock. El endpoint `/ingest-status` expone la última corrida completa + corrida en curso.
4. Circuit breaker + caché TTL agresivo por proveedor (ya identificado en el plan de Mercados): stale data con `data_status: limited` antes que sección vacía. Compartir implementación con lo previsto para `indices.yaml`/`crypto.yaml`.
5. Si en ECO-2 se conservaron `historical:`/`retention:`: implementar job de retención y backfill donde el proveedor lo permita. Si se eliminaron, nada que hacer.

**DoD:** ningún indicador se refetchea más de lo que su `frequency` indica; llamadas de red por ciclo reducidas de forma medible (log comparativo antes/después); `/ingest-status` distingue ejecuciones.

---

### ECO-6 — Frontend y agregación *(~1-2 días, refinable con capturas)*

Resuelve P9. Último a propósito: para entonces los datos que pinta la UI ya son fiables.

**Tareas:**
1. Endpoint agregado `GET /api/market-intelligence/economy/overview` que resuelve en backend el agrupado temático (usando `subcategory`/`priority` del catálogo) y devuelve los bloques que hoy requieren 5 requests. `GLOBAL_PICK`/`THEME_BY_SUBCATEGORY` salen de `EconomyPage.tsx`.
2. Migración de `useEconomyMI`/`useMarketsMI` a TanStack Query (elimina caché manual, SWR y polling artesanales). Condicional: solo si el coste de migración es ≤ al de mantener los dos hooks; si no, unificar los dos hooks en uno parametrizado y posponer react-query.
3. Revisión de estados por sección contra la regla de Fase 6.4: loading / empty / partial / error + provider + quality + última actualización, sin prometer tiempo real.
4. *(Pendiente de capturas)* Incorporar los defectos visuales concretos observados — incluidos los ya conocidos del sprint `PLAN_MEJORA_FABLE5.md`: escalado/moneda de indicadores macro, consistencia de símbolo de divisa.

**DoD:** 1 request inicial en vez de 5 (más polling solo durante ingesta activa); lógica temática fuera de la UI; estados honestos por sección.

---

## Secuencia y dependencias

```
ECO-0 (tests) ──► ECO-1 (contrato) ──► ECO-2 (catálogo) ──► ECO-3 (reglas + ADR almacén)
                                                                │
                                                    [ECO-3b migración, condicional]
                                                                │
                                                                ▼
                                                    ECO-4 (lecturas + impacto) ──► ECO-5 (scheduler) ──► ECO-6 (UI)
```

Estimación total: **9-13 días** de trabajo efectivo (+2 si hay migración de almacén). ECO-0→ECO-2 forman el bloque crítico que resuelve el problema de confianza en los datos; ECO-4→ECO-6 son calidad y eficiencia.

## Fuera de alcance (explícito)

- Scraping o proveedores no oficiales (PMIs de S&P Global quedan fuera salvo licencia futura).
- IA en el pipeline de ingesta (regla del proyecto).
- Rediseño visual de EconomyPage más allá de estados y agregación (pendiente de capturas y de `PLAN_MEJORA_FABLE5.md`).

## Preguntas abiertas para tu revisión

1. **ECO-2, gap INE:** ¿prefieres implementar la API del INE (Tempus) para los 5 indicadores que faltan, o rebajar el primario a Eurostat con serie ES específica? La segunda es más barata; la primera da datos más frescos y respeta la fuente nacional declarada.
2. **ECO-3, tipos BCE:** ¿unificamos en Market Intelligence y el módulo de inversiones lee de ahí (acoplamiento inter-módulo), o mantenemos `ReferenceRateObservation` como copia con contrato de sincronización documentado?
3. **ECO-3b:** ¿tienes uso analítico real previsto para DuckDB a medio plazo (más allá de los datasheets actuales) que justifique conservarlo pese al mono-escritor?
4. **PMIs:** ¿eliminar del catálogo o `disabled: true` con razón visible en el YAML?