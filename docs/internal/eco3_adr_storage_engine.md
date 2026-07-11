# ADR ECO-3 — Motor de almacenamiento del Market Intelligence Layer

- **Estado:** Propuesto (pendiente de aprobación del equipo)
- **Fecha:** 2026-07-06
- **Formato:** engineering:architecture
- **Sprint:** ECO-3 Parte B (spike + ADR). La migración, si se aprueba, es ECO-3b.

## Contexto

El Market Intelligence Layer (MI) persiste en **DuckDB** (`mi_*`), mientras que el resto
de la app (finanzas personales, inversiones) usa **SQLite**. DuckDB opera como
**mono-escritor**: si un segundo proceso abre el fichero, el nuevo cae a una base **en
memoria** y se activa maquinaria de avisos (`is_in_memory`, banners) para no servir datos
fantasma. Esa fragilidad es real en el arranque de un segundo backend / scripts one-shot.

La pregunta de P5: ¿el volumen y el uso justifican DuckDB, o SQLite WAL cubre de sobra
eliminando la fragilidad y unificando a un solo motor?

## Drivers de decisión

- Volumen real: ~72 indicadores, del orden de **decenas de filas/día**.
- Fragilidad del mono-escritor + fallback a memoria (coste operativo actual).
- Dos motores en la misma app (SQLite personal + DuckDB MI) = doble mental model.
- Uso analítico futuro (datasheets IA, agregaciones) — declarado como fuerte de DuckDB.

## Evidencia del spike

**1. Query más compleja portada.** El patrón dominante es "última observación por
partición": DuckDB usa `QUALIFY ROW_NUMBER() OVER (...)`. SQLite no tiene `QUALIFY` pero sí
funciones de ventana desde 3.25 → se porta a subquery:

```sql
-- DuckDB
SELECT ... FROM mi_macro_observations
QUALIFY ROW_NUMBER() OVER (PARTITION BY catalog_item_id ORDER BY retrieved_at DESC) = 1;
-- SQLite equivalente
SELECT cat, period, value FROM (
  SELECT ..., ROW_NUMBER() OVER (PARTITION BY catalog_item_id ORDER BY retrieved_at DESC) rn
  FROM mi_macro_observations) WHERE rn = 1;
```

Port mecánico (3 queries `get_latest_*` + `get_macro_history`), mismo resultado.

**2. Benchmark trivial** (2.880 filas ≈ 72 items × 40 obs, p50 de 200 ejecuciones,
misma máquina):

| Motor | latest-per-partition (p50) | filas out |
|---|---|---|
| SQLite WAL (subquery) | **1.638 ms** | 72 |
| DuckDB (QUALIFY) | 1.663 ms | 72 |

A este volumen la ventaja columnar de DuckDB es **indistinguible del ruido**. El argumento
"uso analítico futuro" es especulativo (YAGNI) con decenas de filas/día; reevaluable si el
volumen crece un par de órdenes de magnitud.

## Decisión (propuesta)

**Migrar el MI a SQLite en modo WAL** (`journal_mode=WAL`, `busy_timeout`), un solo motor
en la app. Elimina la clase de fragilidad del mono-escritor y borra la maquinaria de
`is_in_memory`/banners. La migración es su propio sprint **ECO-3b** (~2 días): DDL `mi_*`,
port de queries `QUALIFY`→CTE, script de migración de datos, borrado de warnings,
actualización de `03_ARCHITECTURE.md` y `15_MARKET_PROVIDERS.md`.

**Alternativa si se conserva DuckDB:** garantizar proceso único por diseño (lockfile con
mensaje claro al arrancar un segundo backend) y documentarlo. No resuelve el doble motor.

## Consecuencias

- (+) Un solo motor, un solo backup, sin fallback-a-memoria ni banners.
- (+) Los scripts one-shot (`purge_clones`, `normalize_periods`) dejan de arriesgar el
  fallback en memoria.
- (−) Coste de migración ECO-3b (acotado; volumen bajo, sin datos críticos históricos).
- (−) Se renuncia a la ventaja columnar de DuckDB, hoy irrelevante por volumen.

---

## Anexo A2 — Contrato de los dos almacenes del tipo BCE

Coexisten dos almacenes del tipo de facilidad de depósito del BCE. **No se unifican**: el
acoplamiento entre módulos no compensa porque sirven **accesos distintos**.

| Almacén | Módulo | Motor | Acceso | Uso |
|---|---|---|---|---|
| `ReferenceRateObservation` | inversiones | SQLite | histórico diario completo (1999→hoy), `get_rate_on(fecha)` | devengo de intereses en **Decimal**, offline |
| `deposit_facility_eurozone` / `tipo_bce` | market_intelligence | DuckDB | último snapshot | dashboard macro |

**Contrato explícito:**
- La **fuente de verdad para cálculo** (intereses) es `ReferenceRateObservation`
  (inversiones). Decimal, por-día, no depende de MI.
- MI mantiene su snapshot macro de forma independiente (ingesta programada del catálogo).
  No es fuente de cálculo; es presentación.
- Ningún GET ingesta (ECO-3 A1): `GET /rates/ecb-deposit-facility` es **solo lectura** y
  devuelve `status: no_data` si la ingesta programada aún no rellenó el cache.
- Si tras la migración a SQLite (ECO-3b) ambos viven en el mismo motor, reevaluar si una
  única tabla de tipos de referencia con dos vistas (histórico vs. snapshot) elimina la
  duplicación sin acoplar módulos.
