# ECO-2 — Matriz de cobertura macro (declarado vs. real)

**Fecha:** 2026-07-06
**Base:** allowlists honestas de ECO-1 + inspección de qué serie emite realmente cada adapter.
**Regla de "cobertura real":** un proveedor cubre un `catalog_item_id` solo si su `fetch(id)`
devuelve al menos un `MacroIndicator` con valor numérico para ese id. `supports()==True` no
basta: bea/census/european_commission (`PublicDatasetAdapter`) devuelven `MacroSeries` con
`observations=[]` (solo comprueban que la URL responde) → **cero valor**.

## Emisores reales y su cobertura (catalog ids)

| Adapter | catalog ids que emite con valor |
|---|---|
| INE | `ipc_general` |
| BLS | `unemployment_usa` |
| FRED | `unemployment_usa`, `fed_funds_rate`, `industrial_production_usa` (INDPRO), `consumer_sentiment_usa` (UMCSENT), `m2_usa` (M2SL) + curva de bonos US |
| ECB | `tipo_bce`, `deposit_facility_eurozone` + pares `eur_*` (forex) |
| Eurostat | `ipc_general`, `inflation_eurozone`, `desempleo_spain`, `unemployment_eurozone` |
| OECD | `pib_spain` (⚠ % QoQ, no "EUR bn") |
| World Bank | `pib_spain` (EUR bn) |
| **BDE** | **ninguno** — su allowlist son claves internas (`spain_10y`, `spain_cpi`, `spain_unemployment`, `ecb_mrr`), **no** catalog ids. No sirve `euribor_3m`/`euribor_12m` (su primario declarado). |
| BEA / Census / European Commission | **ninguno** — sin valor numérico |

## Matriz por indicador (31 macro)

Leyenda: ✔ emite valor · ✗ en cadena pero no emite · — no está en la cadena

### España (macro_spain.yaml)
| indicador | primary | secondary | fallback | **cobertura** |
|---|---|---|---|---|
| ipc_general | ine ✔ | eurostat ✔ | oecd ✗ | **OK** |
| ipc_subyacente | ine ✗ | eurostat ✗ | — | **SIN DATO** |
| pib_spain | ine ✗ | world_bank ✔ | oecd ✔(⚠unidad) | **OK** |
| desempleo_spain | ine ✗ | eurostat ✔ | — | **OK** (eurostat ES) |
| euribor_3m | bde ✗ | ecb ✗ | fred ✗ | **SIN DATO** ⚠crítico |
| euribor_12m | bde ✗ | ecb ✗ | fred ✗ | **SIN DATO** ⚠crítico |
| tipo_bce | ecb ✔ | fred ✗ | — | **OK** |
| produccion_industrial_spain | ine ✗ | eurostat ✗ | — | **SIN DATO** |
| pmi_manufacturero_spain | ine ✗ | — | — | **SIN DATO** (S&P Global, de pago) |
| pmi_servicios_spain | ine ✗ | — | — | **SIN DATO** (S&P Global, de pago) |
| confianza_consumidor_spain | european_commission ✗ | eurostat ✗ | — | **SIN DATO** |
| deficit_spain | eurostat ✗ | oecd ✗ | — | **SIN DATO** |
| deuda_publica_spain | eurostat ✗ | oecd ✗ | — | **SIN DATO** |

### Eurozona (macro_europe.yaml)
| indicador | primary | secondary | **cobertura** |
|---|---|---|---|
| inflation_eurozone | ecb ✗ | eurostat ✔ | **OK** (primary debería ser eurostat) |
| gdp_eurozone | eurostat ✗ | oecd ✗ | **SIN DATO** |
| unemployment_eurozone | eurostat ✔ | — | **OK** |
| industrial_production_eurozone | eurostat ✗ | — | **SIN DATO** |
| pmi_eurozone | eurostat ✗ | — | **SIN DATO** (S&P Global, de pago) |
| deposit_facility_eurozone | ecb ✔ | fred ✗ | **OK** |
| consumer_confidence_eurozone | european_commission ✗ | eurostat ✗ | **SIN DATO** |

### EE.UU. (macro_usa.yaml)
| indicador | primary | secondary | fallback | **cobertura** |
|---|---|---|---|---|
| cpi_usa | bls ✗ | fred ✗ | — | **SIN DATO** |
| core_cpi_usa | bls ✗ | fred ✗ | — | **SIN DATO** |
| gdp_usa | bea ✗ | fred ✗ | world_bank ✗ | **SIN DATO** |
| unemployment_usa | bls ✔ | fred ✔ | — | **OK** |
| fed_funds_rate | fred ✔ | — | — | **OK** |
| nfp_usa | bls ✗ | fred ✗ | — | **SIN DATO** |
| retail_sales_usa | census ✗ | fred ✗ | — | **SIN DATO** |
| housing_starts_usa | census ✗ | fred ✗ | — | **SIN DATO** |
| industrial_production_usa | fred ✔ | — | — | **OK** |
| consumer_sentiment_usa | fred ✔ | — | — | **OK** |
| m2_usa | fred ✔ | — | — | **OK** |

## Resumen

- **Con dato real: 12 / 31.** ipc_general, pib_spain, desempleo_spain, tipo_bce, inflation_eurozone, unemployment_eurozone, deposit_facility_eurozone, unemployment_usa, fed_funds_rate, industrial_production_usa, consumer_sentiment_usa, m2_usa.
- **Sin dato: 19 / 31.** Antes muchos aparecían "llenos" por el bug de clonación (P1); ECO-1 lo cortó y ahora el hueco es visible y honesto.

### Clasificación de los 19 sin dato
| Tipo | Indicadores | Acción ECO-2 |
|---|---|---|
| **Estructuralmente muerto** (proveedor de pago, fuera de alcance) | pmi_manufacturero_spain, pmi_servicios_spain, pmi_eurozone | Quitar del catálogo |
| **Fixable vía FRED** (serie pública, requiere verificar código+unidad en vivo) | cpi_usa, core_cpi_usa, nfp_usa, gdp_usa, retail_sales_usa, housing_starts_usa | Ampliar `fred._INDICATOR_SERIES` |
| **Fixable vía Eurostat** (serie ES/EA con unidad correcta, verificar dataset en vivo) | ipc_subyacente, produccion_industrial_spain, deficit_spain, deuda_publica_spain, gdp_eurozone, industrial_production_eurozone | Ampliar `eurostat._SERIES` |
| **Fixable vía Eurostat/DG-ECFIN** | confianza_consumidor_spain, consumer_confidence_eurozone | Serie de sentimiento Eurostat |
| **Sin fuente pública clara** | euribor_3m, euribor_12m | Buscar fuente (EMMI/ECB); crítico para hipotecas |

**Nota de integridad:** ampliar FRED/Eurostat exige verificar código de serie y unidad contra la
API en vivo. Añadir series "a ciegas" reintroduce exactamente el tipo de bug (dato con unidad
equivocada) que ECO-1 cerró. Por eso las ampliaciones no se hacen sin esa verificación.

---

## Progreso de saneamiento

### Checkpoint 2a (hecho, 2026-07-06)
- **PMIs eliminados** del catálogo: pmi_manufacturero_spain, pmi_servicios_spain, pmi_eurozone.
- **6 USA cerrados vía FRED** (series+unidad verificadas en vivo): cpi_usa (`CPIAUCSL` pc1, %),
  core_cpi_usa (`CPILFESL` pc1, %), gdp_usa (`GDP`, USD bn, trimestral), nfp_usa (`PAYEMS`, miles),
  retail_sales_usa (`RSAFS`, USD mn), housing_starts_usa (`HOUST`, miles).
- Catálogo recableado: gdp/retail/housing pasan a `provider_primary: fred` (bea/census no emiten).
- Metadatos `historical:`/`retention:` marcados como **reserved para ECO-5** (no borrados).
- Cobertura: **12 → 18 / 28** (31 − 3 PMIs = 28 indicadores).

### Checkpoint 2b (hecho, 2026-07-06)
Dataset+filtros+unidad verificados contra la API en vivo antes de implementar.

**8 series cerradas vía Eurostat** (adapter `eurostat._SERIES` ahora lleva unidad/país/escala por serie):

| catalog id | dataset | filtros | geo | unidad |
|---|---|---|---|---|
| ipc_subyacente | prc_hicp_manr | coicop=TOT_X_NRG_FOOD | ES | % |
| gdp_eurozone | namq_10_gdp | CP_MEUR, SCA, B1GQ | EA20 | EUR bn (÷1000 desde millones) |
| deuda_publica_spain | gov_10q_ggdebt | PC_GDP, S13, GD | ES | % PIB |
| deficit_spain | gov_10q_ggnfa | PC_GDP, S13, B9, NSA | ES | % PIB |
| produccion_industrial_spain | sts_inpr_m | PRD, B-D, SCA, I21 | ES | index |
| industrial_production_eurozone | sts_inpr_m | idem | EA20 | index |
| confianza_consumidor_spain | ei_bsco_m | BS-CSMCI, SA, BAL | ES | index |
| consumer_confidence_eurozone | ei_bsco_m | idem | **EA21** (EA20 no publica la celda) | index |

**Euríbor cerrado vía BCE** (no había fuente clara): dataset FM, series `EURIBOR3MD_`/`EURIBOR1YD_`,
**solo mensual** (el daily freq=B fue discontinuado). El catálogo declara `frequency: daily` pero
la realidad pública es mensual → a revisar en ECO-5.

**Recableado de catálogo** (primario → fuente que realmente emite):
- España: ipc_subyacente, produccion_industrial_spain, confianza_consumidor_spain → `eurostat`;
  euribor_3m, euribor_12m → `ecb`.
- Eurozona: inflation_eurozone, consumer_confidence_eurozone → `eurostat`.

**Cobertura tras 2b: 28 / 28** indicadores con dato real (todos los que quedan tras quitar los 3 PMIs).
Los únicos sin fuente pública gratuita eran los PMI (S&P Global), ya eliminados.

Test: `test_eurostat_coverage.py` (unidad+escala+geo por serie, Euríbor por BCE), sin red.
