---
name: GLOSARIO
description: Glosario de dominio y nombres de entidades reales del modelo — para no re-derivar leyendo código
metadata:
  type: reference
---

# 📖 Glosario de dominio

Términos del negocio y **nombres exactos** de entidades/servicios del código. Ante duda de dominio,
mira aquí antes de leer código. Detalle en [[MOC - Dominio]] y [[04_DATA_MODEL]].

## Entidades del modelo
- **Holding** — posición de un activo (acción, fondo, cuenta remunerada) en una cuenta.
- **HoldingValueHistory** — histórico de valor de acciones/ETF (vía yfinance).
- **FundValuationSnapshot** — snapshot de valoración de fondo (`date`, `market_value`, `contributed_total`; único holding+date).
- **SavingsAccountConfig** — config de cuenta remunerada, keyed por `account_id` (`opened_at`, `rate_source`, `fixed_rate`, `spread_bps`).
- **ReferenceRateObservation** — histórico del tipo de referencia BCE (DFR) cacheado en SQLite (keyed por rate_id+effective_date).
- **Transaction** — movimiento; las aportaciones a ahorro son `type=transfer` sobre la Account.
- **Account** — cuenta financiera del usuario.

## Servicios / conceptos
- **savings_service** — motor de interés compuesto mensual; tipo del último día del mes; modo inverso retro-calcula saldo inicial.
- **reference_rate_service** — carga DFR del BCE (ECB SDMX, fallback FRED CSV `ECBDFR`, sin API key).
- **Reconciliation** — `_compute_quality_state` clasifica calidad por `asset.asset_type` (Mercado/Manual/Calculado).
- **forward-fill** — relleno hacia delante de la serie mensual agregada del portfolio.

## Siglas
- **DFR** — Deposit Facility Rate (tipo de la facilidad de depósito del BCE).
- **BCE / ECB** — Banco Central Europeo.
- **RAG** — Retrieval-Augmented Generation (ver [[24_DOCUMENT_INTELLIGENCE_RAG]]).
- **MOC** — Map of Content (nota-índice de Obsidian).

## Restricciones transversales del dominio
Decimal siempre; nada se crea sin confirmación; la IA queda fuera del cálculo financiero. Ver [[project_constraints]].

---
**Relacionadas:** [[MOC - Dominio]] · [[04_DATA_MODEL]] · [[project_investments_module]] · [[project_constraints]]

Tags: #referencia #dominio #glosario
