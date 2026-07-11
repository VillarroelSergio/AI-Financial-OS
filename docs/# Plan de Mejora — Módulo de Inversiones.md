# Plan de Mejora — Módulo de Inversiones

**Proyecto:** AI Financial OS
**Fecha:** 2026-07-05
**Alcance:** Rediseño del módulo Inversiones para soportar tres tipos de activo (acciones, fondos de inversión, cuentas remuneradas) con flujos de alta, actualización y edición diferenciados.
**Referencias:** `04_DATA_MODEL.md`, `11_API_CONTRACT.md`, `20_PORTFOLIO_IMPORT_ASSISTANT.md`, `22_PORTFOLIO_RECONCILIATION_ANALYTICS.md`, `12_DEVELOPMENT_WORKFLOW.md`, `15_MARKET_PROVIDERS.md`

---

## 1. Diagnóstico desde las capturas

### BUG-INV-1 — Rentabilidad global imposible (CRÍTICO)
La cabecera muestra: Valor total 23.871,36 € / Aportado 90.857,52 € / Rentabilidad **−66.986,16 € (−73,73%)**.
Causas probables combinadas:
- **Duplicados**: dos posiciones BBVA.MC (323,36 € y 4.548,00 €) conviven; el "Aportado" suma el coste de ambas.
- **Fondos a 0,00 €**: Vanguard US 500 y Cleome Index aparecen con valor 0 € (no hay precio de mercado para clases institucionales de Finizens) pero su coste sí computa en "Aportado".
- **Cuenta remunerada (19.000 €)** mezclada en el cálculo de rentabilidad de mercado: su "coste" infla el aportado sin lógica de intereses propia.

**Conclusión de diseño:** el KPI global no puede sumar tipos de activo con semánticas distintas sin normalizar cada uno con su propio motor de valoración.

### BUG-INV-2 — Fondos de inversión no cargables ni valorables
Los fondos de Finizens (clases institucionales, sin ticker cotizado público) no tienen cobertura de precio en los proveedores actuales (`coverage_status = UNAVAILABLE`). El flujo actual intenta tratarlos como acciones → valor 0 €. El modelo correcto es **valoración manual con snapshots periódicos** (como muestra la propia app de Finizens: fondo + € + rendimiento % y €).

### BUG-INV-3 — Cuentas remuneradas sin modelo propio
"Cuenta Remunerada Trade Republic" existe como posición plana de 19.000 €. No hay concepto de fecha de apertura, tipo de interés, ni intereses generados.

### BUG-INV-4 — Panel por broker vacío
"Sin posiciones en este broker" en Trade Republic y Finizens pese a existir posiciones. Los holdings no están vinculados (o no se filtran) por `account_id` → broker.

### BUG-INV-5 — "Sin histórico de precios para BBVA.MC"
El detalle expandido de posición no encuentra serie histórica aunque el precio actual sí resuelve. Falta ingesta/persistencia de histórico o el lookup usa una clave distinta a la de ingesta.

### BUG-INV-6 — Sin edición
No existe forma de editar cantidad, precio de entrada, cuenta o eliminar/fusionar una posición desde la UI. Corregir BUG-INV-1 manualmente es hoy imposible para el usuario.

---

## 2. Modelo de dominio propuesto

### 2.1 Tres tipos de activo, tres motores de valoración

| Tipo | Alta | Valoración | Rendimiento |
|---|---|---|---|
| **Acción / ETF cotizado** | Flujo actual (ticker + cantidad + precio entrada) | Precio de mercado automático | (precio_actual − precio_entrada) × cantidad |
| **Fondo de inversión** | Nombre + cuenta + aportado + valor actual + fecha | **Snapshot manual periódico** | valor_último_snapshot − aportado_acumulado |
| **Cuenta remunerada** | Nombre + saldo + fecha de apertura (+ movimientos opcionales) | **Cálculo determinista con tipo BCE** | Σ intereses mensuales calculados |

### 2.2 Nuevas entidades (SQLite)

#### FundValuationSnapshot
Serie temporal de valor de un fondo, introducida por el usuario. Alimenta la gráfica de evolución.

```txt
id                  UUID
holding_id          FK → Holding (asset_type = fund, price_source = manual)
date                ISO date
market_value        Decimal   # Valor total de la posición ese día
contributed_total   Decimal   # Aportado acumulado a esa fecha (opcional; si null, se hereda)
note                Text opcional
created_at / updated_at
```

Reglas:
- Un snapshot por fondo y fecha (constraint UNIQUE holding_id + date).
- Rendimiento en fecha t = market_value(t) − contributed_total(t).
- Las aportaciones nuevas se registran como `InvestmentOperation` tipo `deposit` (entidad ya existente) y actualizan `contributed_total`.
- El último snapshot fija `Holding.market_value` y `valuation_date`.

#### SavingsAccountConfig
Configuración de una cuenta remunerada sobre una `Account` existente (`type = savings`).

```txt
id                  UUID
account_id          FK → Account
opened_at           ISO date
rate_source         ecb_deposit_facility | fixed | manual
fixed_rate          Decimal opcional  # solo si rate_source = fixed
spread_bps          Integer, default 0  # ajuste sobre el tipo de referencia
compounding         monthly (V1)
created_at / updated_at
```

Movimientos (aportaciones/retiradas) se registran como `Transaction` tipo `transfer` sobre la cuenta — reutiliza el modelo existente, sin tabla nueva.

#### Histórico del tipo BCE
Reutilizar `EconomicIndicator` + `EconomicObservation` ya existentes:
- Nuevo indicador `ECB_DEPOSIT_FACILITY` (region: eurozone, category: rates, frequency: irregular).
- Fuente compatible con las constraints (API oficial, sin scraping): **ECB Data Portal (SDMX REST)** serie `FM.D.U2.EUR.4F.KR.DFR.LEV`, o **FRED** serie `ECBDFR` como fallback (ya hay adapter FRED en `15_MARKET_PROVIDERS.md`).
- Se ingesta una vez el histórico completo desde 2020 (o desde la fecha de apertura más antigua) y se refresca con el snapshot macro habitual.

### 2.3 Motor de cálculo de cuenta remunerada (determinista, sin IA)

Para cada mes m desde `opened_at` hasta hoy:

```txt
tipo_m        = tipo BCE vigente el último día del mes m + spread
interés_m     = saldo_inicio_m × tipo_m / 12
saldo_fin_m   = saldo_inicio_m + interés_m + aportaciones_m − retiradas_m
```

Salida: serie mensual `[{month, rate, interest, balance}]` + `total_interest`. Decimal siempre, nunca float (convención `04_DATA_MODEL.md`).

Nota V1: si el usuario solo conoce el **saldo actual**, se ofrece modo inverso: dado saldo_actual y opened_at, se retro-calcula el saldo inicial asumiendo sin movimientos, y se marca como `estimated`. El usuario puede refinar añadiendo movimientos.

### 2.4 Reglas de agregación de KPIs (fix BUG-INV-1)

```txt
Valor total    = Σ acciones (mercado) + Σ fondos (último snapshot) + Σ cuentas (saldo calculado)
Aportado       = Σ coste acciones + Σ contributed_total fondos + Σ (inicial + aportaciones netas) cuentas
Rentabilidad € = Valor total − Aportado
Rentabilidad % = Rentabilidad € / Aportado, mostrada TAMBIÉN desglosada por tipo
```

Regla de honestidad (coherente con QualityEngine): si algún componente es `estimated` o tiene snapshot > 60 días, el KPI global muestra badge de calidad, nunca un número roto en silencio.

---

## 3. API (extensión de `11_API_CONTRACT.md`)

### Holdings — edición (fix BUG-INV-6)
```txt
PUT    /api/investments/holdings/{id}        # cantidad, average_price, account_id, name
DELETE /api/investments/holdings/{id}
POST   /api/investments/holdings/merge       # Body: { source_id, target_id } → fusiona duplicados
```

### Fondos
```txt
POST   /api/investments/funds                          # alta: name, account_id, contributed, value, date
GET    /api/investments/funds/{holding_id}/snapshots
POST   /api/investments/funds/{holding_id}/snapshots   # { date, market_value, contribution? }
PUT    /api/investments/funds/snapshots/{id}
DELETE /api/investments/funds/snapshots/{id}
```

### Cuentas remuneradas
```txt
POST   /api/investments/savings                        # alta: account_id | new_account, opened_at, balance, rate_source, spread_bps
GET    /api/investments/savings/{id}/projection        # serie mensual + total_interest
PUT    /api/investments/savings/{id}                   # editar config
DELETE /api/investments/savings/{id}
```

### Tipo BCE
```txt
GET    /api/market-intelligence/rates/ecb-deposit-facility?from=YYYY-MM-DD
```
(interno; la UI de cuentas lo consume vía backend, nunca directamente).

---

## 4. UX propuesta

### 4.1 Estructura del módulo
```txt
Inversiones
├── Resumen (KPIs desglosados por tipo + gráfica agregada de evolución)
├── Tab Acciones      → tabla actual + botones Editar / Eliminar por fila
├── Tab Fondos        → tarjetas estilo Finizens (nombre, €, rendimiento % y €)
│                       + botón "Actualizar valor" + gráfica por fondo
├── Tab Cuentas       → tarjeta por cuenta: saldo, intereses totales, tipo vigente
│                       + gráfica mensual de saldo e intereses
└── Importar / Seguimiento (existentes)
```

### 4.2 Alta unificada
El botón **"+ Añadir"** abre un selector de tipo con tres caminos:

1. **Acción/ETF** → flujo actual (resolve_asset, validación, confirmación).
2. **Fondo** → formulario: nombre libre, cuenta/broker, aportado hasta hoy, valor actual, fecha. Sin resolución de ticker; `price_source = manual`, `asset_type = fund`. Crea el holding + primer snapshot.
3. **Cuenta remunerada** → formulario: nombre, entidad, saldo, fecha de apertura, tipo (por defecto "BCE facilidad de depósito"). Al confirmar, muestra preview de la serie calculada antes de guardar ("intereses estimados desde apertura: X €").

### 4.3 Actualización periódica de fondos
- CTA visible en cada tarjeta de fondo: "Actualizar valor" → modal con dos campos (valor, fecha, aportación opcional). Objetivo: <10 segundos por actualización.
- Insight suave (vía Insights Engine, regla nueva `fund_stale_valuation`): "El fondo X lleva 45 días sin actualizar".
- Cada snapshot añade un punto a la gráfica de evolución (recharts, mismo patrón que Goals).

### 4.4 Edición
Cada fila/tarjeta expone menú contextual: Editar, Eliminar, Fusionar con… (solo si hay candidato duplicado por ticker normalizado, reutilizando `check-duplicates`).

---

## 5. Plan de sprints

Convenciones de `12_DEVELOPMENT_WORKFLOW.md`: ramas `feature/*`, DoD (compila, no rompe rutas, loading/error/empty, tipos, tests para cálculo, docs actualizadas, sin dependencias cloud obligatorias).

### Sprint INV-1 — `feature/investments-data-integrity` (blocker)
Arreglar los datos antes de construir encima.
- Fix cálculo Aportado/Rentabilidad: excluir holdings sin valoración válida del % global o marcar calidad (BUG-INV-1).
- Endpoint + UI mínima de merge de duplicados; fusionar las dos posiciones BBVA (BUG-INV-1).
- Vincular holdings ↔ account/broker y arreglar el filtro del panel por broker (BUG-INV-4).
- Diagnóstico y fix del histórico BBVA.MC (BUG-INV-5): verificar clave de lookup vs ingesta.
- Tests: cálculo de KPIs con cartera mixta, merge, filtro por broker.

### Sprint INV-2 — `feature/investments-domain-model`
- Migraciones: `FundValuationSnapshot`, `SavingsAccountConfig`.
- Indicador `ECB_DEPOSIT_FACILITY` + adapter de ingesta histórica (ECB SDMX, fallback FRED).
- Actualizar `04_DATA_MODEL.md` y `11_API_CONTRACT.md` (aprovecha para cerrar DOC-13 del audit).
- Tests: constraint de snapshot único, ingesta de serie BCE.

### Sprint INV-3 — `feature/investments-funds-flow`
- Endpoints de fondos (alta + CRUD snapshots).
- UI: alta de fondo, tarjetas estilo Finizens, modal "Actualizar valor", gráfica de evolución por fondo.
- Regla de insight `fund_stale_valuation`.
- Tests: rendimiento € y % con aportaciones intermedias.

### Sprint INV-4 — `feature/investments-savings-flow`
- Motor determinista de intereses mensuales (servicio + tests exhaustivos: cambios de tipo mid-period, aportaciones, modo inverso estimado).
- Endpoints de cuentas remuneradas.
- UI: alta con preview, tarjeta con intereses totales y tipo vigente, gráfica mensual saldo/intereses.

### Sprint INV-5 — `feature/investments-edit-ux`
- PUT/DELETE holdings + formularios de edición para los tres tipos.
- Menú contextual unificado (Editar / Eliminar / Fusionar).
- Recalculo reactivo de KPIs tras cada edición.

### Sprint INV-6 — `feature/investments-summary-redesign`
- Rediseño de la cabecera: KPIs con desglose por tipo + badges de calidad.
- Gráfica agregada de evolución de la cartera (mercado + snapshots + saldos calculados).
- Integración con Reconciliation (`22_...md`): los fondos manuales aparecen como `manual`, cuentas como `confirmed` con fuente `calculated`.
- QA manual con los datos reales de las capturas como casos de prueba.

---

## 6. Decisiones y restricciones respetadas

- **Sin scraping ni conexión a bancos/brokers**: fondos → entrada manual con snapshots; cuentas → cálculo determinista con dato macro oficial ya presente en la arquitectura.
- **IA fuera del cálculo**: todo el motor de intereses y rendimientos es determinista; la IA local solo podrá explicar resultados vía datasheet, como en Insights.
- **Decimal, nunca float** en todos los cálculos nuevos.
- **Nada se crea sin confirmación explícita** (preview antes de guardar la cuenta remunerada, revisión antes de merge).

## 7. Riesgos

| Riesgo | Mitigación |
|---|---|
| Serie BCE incompleta u offline | Cachear histórico completo en `EconomicObservation`; el cálculo funciona sin red una vez ingestado |
| Trade Republic no replica exactamente el tipo BCE (fechas valor, cambios intra-mes) | Documentar que es estimación; `spread_bps` y modo `fixed` permiten ajustar; discrepancia mostrada si el usuario introduce saldo real |
| Usuario con snapshots de fondo muy espaciados | Gráfica interpola visualmente pero marca puntos reales; insight de staleness |
| Merge de duplicados destruye datos | Merge conserva ambos históricos de operaciones bajo el holding destino; sin borrado físico de operations |