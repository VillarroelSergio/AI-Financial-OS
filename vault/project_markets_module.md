---
name: project_markets_module
description: Plan UX Mercados — MKT-6/7/8 + auto-backfill hechos; fuentes de histórico por familia
metadata: 
  node_type: memory
  type: project
  originSessionId: 85ebc625-5865-4d3b-a0d3-f2c72c51e2a4
---

Rework del módulo Mercados (plan en `AI-Financial-OS/docs/PROPUESTA_UX_MERCADOS.md`): de tabla pasiva a terminal navegable con ficha de instrumento (gráfico histórico, stats, calidad). Estado a 2026-07-12 (sin commit):

**Hecho:**
- **MKT-6** backend: endpoint de histórico EOD + `backfill_all` multi-proveedor idempotente (DELETE+INSERT por item/symbol/date).
- **MKT-7** frontend: ficha `InstrumentDetailPage` con rangos honestos (1m/3m/6m/1y…); Δ y color se basan en el rango seleccionado (firstClose→lastClose / `range_change_pct`), NO en el cambio del día. ReferenceLine en firstClose.
- **MKT-8** sparklines en filas (batch `GET /sparklines`) + botón "Preguntar a la IA" contextual en la ficha. Filas de forex ahora navegables.
- **Auto-backfill en 1er arranque** (startup.py): `_backfill_history_once` = `backfill_all(years=5, only_missing=True)` una vez; `_refresh_history_if_due` refresca 1y cada >24h. Todo en el daemon background, nunca en un GET.

**Fuentes de histórico por familia** (Stooq CSV quedó bloqueado por JS-challenge):
- índices/commodities → **Yahoo Chart** (`fetch_stooq_history`, se mantuvo el nombre; provider persistido = "yahoo").
- cripto → **CoinGecko** `market_chart` (free tier tope 365 días = 1y).
- forex → **Frankfurter/BCE** (`_FOREX_IDS` lista fija de 8 pares).

`HistoricalPrice` no tiene campo `currency`; los fetchers lo setean dinámico (`rec.currency=...`) y `persist_historical_prices` lo lee con getattr.

Datos ya cargados: ~31.849 filas (20.141 índices/commodities + 11.708 cripto+forex). Ver [[project_constraints]], [[feedback_ux_snapshots]].


---
**Relacionadas:** [[project_economy_plan]] · [[project_constraints]]

Tags: #módulo #decisión
