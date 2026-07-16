# 07 - Economic Intelligence

## Estado actual

La inteligencia economica ya no vive en un modulo independiente `economic_data`.
Actualmente forma parte de Market Intelligence:

```txt
backend/app/modules/market_intelligence/
```

La UI consume estos datos mediante `/api/market-intelligence/*`.

## Objetivo de producto

La seccion economica debe explicar como el contexto macro puede afectar al dinero,
gastos, ahorro, inversiones u objetivos del usuario. No pretende ser un portal
macroeconomico generico.

## Cobertura

Regiones principales:

- Espana.
- Eurozona / Europa.
- Estados Unidos.

Tipos de datos:

- Inflacion.
- Paro.
- PIB y actividad.
- Tipos de interes.
- Bonos.
- Indices relevantes.
- Divisas.
- Noticias financieras seleccionadas cuando aportan contexto.

## Implementacion vigente

```txt
Catalog YAML
  -> ProviderOrchestrator
  -> adapters macro/mercado/noticias
  -> QualityEngine
  -> DuckDB (`mi_*`)
  -> API `/api/market-intelligence/snapshot/macro`
  -> EconomyPage / AI datasheet
```

## Endpoints relacionados

| Endpoint | Uso |
|---|---|
| `GET /api/market-intelligence/snapshot/macro` | Snapshot macro por region |
| `GET /api/market-intelligence/personal-impact` | Impacto personal determinista |
| `GET /api/market-intelligence/ai-datasheet` | Contexto compacto para IA |
| `GET /api/market-intelligence/ingest-status` | Estado de ingesta |

## Reglas

- Mostrar siempre fecha, fuente y `quality_score` cuando aplique.
- Separar calculo determinista de explicacion IA.
- No permitir SQL libre desde el modelo.
- No consultar proveedores live desde la IA; usar backend y datasheets.
- Mantener el foco en impacto personal, no en cobertura macro exhaustiva.
