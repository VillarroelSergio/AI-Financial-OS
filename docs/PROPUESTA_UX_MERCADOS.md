# Propuesta UX/UI — Módulo Mercados: detalle con histórico

Fecha: 2026-07-11
Complementa a: `PLAN_MEJORA_MERCADOS_V3.md` (sprints MKT-D a MKT-5)
Referencia visual del usuario: ficha de instrumento estilo Yahoo Finance (IBEX 35, gráfico intradía, rangos 1d/5d/1m/6m/1a/5a, cierre anterior, rango diario, 52 semanas).

---

## 1. Objetivo de producto

Convertir Mercados de una tabla de lectura pasiva en un terminal navegable: **cada fila es clicable** y abre la ficha del instrumento con su histórico, contexto y metadatos de calidad. Responde a la secuencia Resumen → Explicación → Detalle → Acción del doc 01.

## 2. Realidad de datos (honestidad primero)

Lo que la referencia de Yahoo tiene y nosotros NO podemos prometer en local-first:

| Elemento Yahoo | Viable aquí | Motivo |
|---|---|---|
| Gráfico intradía (1d, ticks por hora) | ❌ | Providers gratuitos (Stooq, ECB, CoinGecko free) sirven EOD/diario; no hay streaming |
| Volumen | ⚠️ Parcial | Stooq lo trae para índices/acciones; no para forex/bonos |
| Rangos 1m / 6m / 1a / 5a / Todos | ✅ | Stooq da histórico EOD completo; CoinGecko da diario para cripto |
| Cierre anterior, apertura, rango diario | ✅ | Campos OHLC del EOD |
| Rango 52 semanas | ✅ | Calculable en SQL sobre la serie |
| Eventos clave | ❌ V1 | Fuera de alcance |

**Regla ECO-2 aplicada**: el selector de rango solo muestra los rangos que la serie local realmente cubre. Si solo hay 3 meses ingestados, no existe botón "5a" deshabilitado ni gráfico vacío: los rangos se derivan de `MIN(date)` de la serie. Nada de prometer intradía: la ficha dice "Datos de cierre diario" junto a la fecha del último dato.

## 3. Modelo de interacción

```
Pestaña (Índices & Cripto / Materias primas / Divisas / Bonos)
  → click en fila
    → Ficha de instrumento (vista detalle, misma página con ruta propia
      /markets/:indicatorCode para que sea enlazable y navegable con atrás)
```

Ficha (de arriba a abajo, patrón Mercury):

1. **Cabecera**: nombre + región, valor grande, Δ absoluto y % con color/flecha, "Al cierre: {fecha del último dato}". Badge `DataStatusBadge` por instrumento (provider, quality_score, frescura) — el mismo componente por fila introducido en P0-02.
2. **Selector de rango**: `1m · 3m · 6m · 1a · 5a · Todo` (solo los cubiertos por la serie). Sin "1d": no hay intradía y no se finge.
3. **Gráfico de área** (recharts, como en Goals): una serie, línea de referencia en cierre anterior, tooltip con fecha+valor, min/max del rango anotados. Volumen como barra secundaria solo si la serie lo trae.
4. **Panel de estadísticas** (grid 2×3, estilo del footer de Yahoo): cierre anterior, apertura, rango del día, rango 52 semanas, variación del rango seleccionado, volumen (si existe).
5. **Metadatos de calidad**: provider primario, último refresh, nº de observaciones de la serie, huecos detectados. Esto es lo que Yahoo no tiene y tu producto sí debe tener.
6. **"Preguntar a la IA"** contextual (patrón INS-8): abre el asistente con `selected_entity = indicator_code`. La IA explica la serie vía tool determinista, nunca la recalcula.

Extra de bajo coste en la tabla: **sparkline** por fila (últimas ~30 observaciones), reutilizando el patrón `history` de 13 puntos que el snapshot macro ya expone. Da vida a la tabla y anticipa el click.

## 4. Contrato API propuesto

### GET `/api/market-intelligence/history/{indicator_code}?range=1m|3m|6m|1y|5y|max`

```json
{
  "indicator_code": "ibex35",
  "name": "IBEX 35",
  "region": "es",
  "currency": "EUR",
  "provider_id": "stooq",
  "quality_score": 0.94,
  "last_updated": "2026-07-10",
  "granularity": "eod",
  "available_ranges": ["1m", "3m", "6m", "1y", "max"],
  "stats": {
    "previous_close": 19322.80,
    "open": 19333.70,
    "day_low": 19318.00,
    "day_high": 19443.90,
    "week52_low": 13855.50,
    "week52_high": 19879.10,
    "range_change_pct": 12.4,
    "volume": 107858866
  },
  "series": [
    { "date": "2026-06-11", "close": 18990.10, "volume": 98211002 },
    { "date": "2026-06-12", "close": 19015.40, "volume": null }
  ]
}
```

Reglas:
- Lee exclusivamente de `mi_historical_prices` (SQLite WAL, `get_conn()`). **Nunca ingesta síncrona en el GET** — regla ya establecida en el plan ECO. Si la serie es corta, devuelve lo que hay + `available_ranges` honestos.
- `stats` se calcula en SQL determinista en el backend; el frontend no computa nada financiero.
- Downsampling en servidor para rangos largos (p.ej. máx ~400 puntos por respuesta) para mantener el gráfico fluido.

### Backfill (necesario para que "5a" exista)

Comando CLI del módulo (patrón `cli/` existente): `backfill-history --catalog indices,forex,crypto --years 5`, idempotente (DELETE+INSERT por `(indicator_code, date)`), manual y bajo demanda — nunca en el arranque, para no penalizar el tiempo de arranque <5s de Fase 11. La UI puede exponer "Descargar histórico completo" en Ajustes más adelante.

## 5. Componentes frontend

```
apps/desktop/src/features/markets/
├── MarketsPage.tsx            (existente — filas ahora navegables + sparkline)
├── detail/
│   ├── InstrumentDetailPage.tsx    (ruta /markets/:indicatorCode)
│   ├── RangeSelector.tsx
│   ├── PriceChart.tsx              (recharts area, ref-line cierre anterior)
│   ├── StatsGrid.tsx
│   └── QualityMetaPanel.tsx
└── components/RowSparkline.tsx
```

Mercury: `PageHeader` común, `premium-card` para gráfico y stats, acento violet-blue solo en el rango activo, radios 8px, sin UUIDs visibles (la ruta usa `indicator_code` legible: `/markets/ibex35`).

## 6. Sprints (continúan la numeración del plan V3)

### MKT-6 — Backend histórico (1–1,5 días)
- Endpoint `history/{indicator_code}` + stats SQL + downsampling.
- CLI de backfill idempotente (Stooq para índices/commodities, CoinGecko para cripto, ECB SDMX para forex).
- Tests: contrato del endpoint, stats correctos con serie sintética, rangos honestos con serie corta, idempotencia del backfill.

### MKT-7 — Ficha de instrumento (1,5–2 días)
- Ruta navegable, cabecera, selector de rango, gráfico, stats, metadatos de calidad, botón IA contextual.
- Estados loading/empty/error cuidados: serie vacía → "Sin histórico local aún" + CTA de backfill.
- `npx tsc --noEmit` limpio; snapshot UX de la nueva ruta añadida a `snapshot-routes.ts`.

### MKT-8 — Sparklines en tabla (0,5 día, opcional)
- `RowSparkline` con las últimas ~30 observaciones servidas en el propio snapshot (evitar N llamadas por fila: el snapshot añade un campo `spark: number[]`).

**Prerequisito duro**: MKT-1 (integridad Divisas) cerrado antes de MKT-6/7. Dar una ficha con histórico a series contaminadas (7 pares clonados de EUR/USD) multiplicaría el daño: el gráfico dibujaría con confianza datos falsos.

## 7. Decisiones abiertas UX

1. **Vista detalle**: ¿página con ruta propia (propuesto — enlazable, botón atrás, snapshot UX) o drawer lateral (más ligero, menos navegación)?
2. **Profundidad de backfill por defecto**: ¿1 año (rápido, ~250 filas/instrumento) o 5 años? Propuesta: 1 año automático tras primer uso + botón "Descargar 5 años" explícito.
3. **Sparklines (MKT-8)**: ¿incluir en esta tanda o después de la release de Fase 11? Propuesta: después, es puro polish.
4. **Cripto y granularidad**: CoinGecko free da diario; ¿aceptamos que Bitcoin tenga la misma granularidad EOD que el IBEX (propuesto) o se busca provider horario más adelante?

## 8. Estimación

| Sprint | Esfuerzo |
|---|---|
| MKT-6 | 1–1,5 días |
| MKT-7 | 1,5–2 días |
| MKT-8 (opcional) | 0,5 día |
| **Total UX** | **3–4 días** (tras cerrar MKT-1) |
