# 04 — Data Model

## Objetivo

Definir un modelo de datos inicial suficientemente sólido para soportar cuentas, movimientos, categorías, inversiones, objetivos, importaciones, datos de mercado y datos macroeconómicos.

## Convenciones

- IDs internos UUID.
- Fechas en ISO `YYYY-MM-DD`.
- Datetimes en UTC.
- Importes en decimal, nunca float en lógica financiera.
- Moneda ISO 4217.
- Tablas con `created_at` y `updated_at`.
- Importaciones trazables mediante `import_batch_id`.

## Entidades principales

### Account

Representa una cuenta financiera.

```txt
id
name
type: cash | bank | broker | savings | investment | mortgage | other
institution
currency
current_balance
is_active
created_at
updated_at
```

Ejemplos:

- Monefy / Efectivo.
- BBVA.
- Revolut.
- Trade Republic efectivo.
- Trade Republic cartera.
- Finizens.
- Cuenta remunerada.

### Category

```txt
id
name
parent_id
type: income | expense | transfer | investment
icon
color
is_system
created_at
updated_at
```

Categorías iniciales inspiradas en Monefy:

- Alimentación.
- Restaurante.
- Casa.
- Transporte.
- Ocio.
- Comunicaciones.
- Salud.
- Mascotas.
- Regalos.
- Ropa.
- Deportes.
- Salario.
- Ahorros.
- Depósitos.
- Otros.

### Transaction

```txt
id
account_id
category_id
date
description
amount
currency
converted_amount
converted_currency
type: income | expense | transfer | investment
source: manual | csv | pdf | system
source_name
external_id
import_batch_id
notes
created_at
updated_at
```

Reglas:

- Amount positivo: ingreso.
- Amount negativo: gasto.
- Transferencias deben representarse con tipo `transfer` cuando se detecten.
- En V1 se permite importar sin resolver transferencias automáticamente.

### ImportBatch

```txt
id
source_name
source_type: monefy | bbva | revolut | trade_republic | finizens | generic_csv
file_name
file_hash
status: pending | validated | imported | failed | rolled_back
rows_total
rows_imported
rows_failed
created_at
completed_at
```

### ImportRow

```txt
id
import_batch_id
row_number
raw_payload_json
normalized_payload_json
status: pending | valid | invalid | duplicate | imported
error_message
created_at
```

### DuplicateCandidate

```txt
id
transaction_id
candidate_transaction_id
score
reason
created_at
```

## Inversiones

### InvestmentAsset

```txt
id
name
ticker
isin
asset_type: stock | etf | fund | bond | crypto | cash | other
currency
region
sector
created_at
updated_at
```

### Holding

```txt
id
account_id
asset_id
quantity
average_price
current_price
market_value
currency
valuation_date
created_at
updated_at
```

### InvestmentOperation

```txt
id
account_id
asset_id
date
operation_type: buy | sell | dividend | interest | fee | deposit | withdrawal
quantity
price
amount
currency
fees
source
import_batch_id
created_at
updated_at
```

## Objetivos

### Goal

```txt
id
name
type: emergency_fund | housing | investment | savings | custom
target_amount
current_amount
target_date
monthly_contribution
priority: low | medium | high
status: active | completed | paused
created_at
updated_at
```

## Datos de mercado

### MarketInstrument

```txt
id
symbol
name
instrument_type: index | fx | bond | crypto | stock | etf
region
currency
source
created_at
updated_at
```

### MarketObservation

```txt
id
instrument_id
date
open
high
low
close
previous_close
change_absolute
change_percent
currency
source
created_at
```

## Datos macroeconómicos

### EconomicIndicator

```txt
id
code
name
region: spain | eurozone | united_states
category: inflation | labour | growth | rates | bonds | currency | market
frequency: daily | monthly | quarterly | yearly | irregular
unit
source
description
created_at
updated_at
```

### EconomicObservation

```txt
id
indicator_id
date
period
value
unit
source_release_date
is_revised
created_at
```

## Settings

```txt
id
key
value_json
created_at
updated_at
```

Ejemplos:

- `app.language = es`.
- `theme.mode = dark`.
- `ai.provider = ollama`.
- `ai.model = qwen`.
- `security.level = basic`.

## Importación de cartera (Portfolio Import)

Las siguientes entidades no se persisten: son estructuras en memoria/API para el flujo de importación asistida.

### RawPosition (in-memory)

```txt
raw_name        # Nombre tal como aparece en el texto del broker
quantity        # Número de participaciones/acciones (opcional)
current_value   # Valor de mercado en el momento de la captura (opcional)
currency        # Divisa detectada (EUR, USD, GBP, AUD)
return_pct      # Rentabilidad % desde inicio (opcional, puede ser negativa)
estimated_cost  # Calculado: current_value / (1 + return_pct/100)
```

### ValidatedPosition (API response)

Extiende RawPosition con resolución de instrumento y cobertura de precio:

```txt
ticker               # Resuelto por resolve_asset()
name                 # Nombre oficial del instrumento
market               # Bolsa de cotización
current_price        # Precio actual en divisa del instrumento
eur_value            # Valor en EUR (via FX conversion)
resolution_status    # found | ambiguous | unavailable
coverage_status      # OK | FX_PENDING | UNAVAILABLE
import_status        # READY | REQUIRES_CONFIRMATION | NO_PRICE | MANUAL | REVIEW
requires_confirmation
confirmation_reason
```

## Simulaciones de objetivos (Goals Simulations)

Ninguna de estas estructuras persiste en base de datos. Se calculan en cada petición.

### SimulationResult (API response)

```txt
goal_id
current_amount
target_amount
monthly_contribution
inflation_rate
inflation_adjusted_target   # target × (1+inflation)^(meses/12)
monthly_data[]              # MonthlyDataPoint por mes 0..120
scenarios[]                 # ScenarioProjection × 3
target_date
generated_at
```

### MonthlyDataPoint

```txt
month          # 0 = hoy
label          # "Jun 2026"
conservative   # Saldo escenario conservador (2%)
base           # Saldo escenario base (6%)
optimistic     # Saldo escenario optimista (10%)
```

### ScenarioProjection

```txt
scenario                  # conservative | base | optimistic
label                     # Conservador | Base | Optimista
color                     # Hex CSS
annual_growth_rate        # 0.02 | 0.06 | 0.10
months_to_target          # null si no se alcanza en max_months
projected_date            # ISO date o null
achievable_by_target_date # bool o null (solo si el objetivo tiene fecha)
final_amount
```

## Campos derivados no persistentes

Estos valores deben calcularse en servicios o vistas:

- Patrimonio neto.
- Liquidez.
- Gasto mensual.
- Ingreso mensual.
- Tasa de ahorro.
- Rentabilidad total.
- Rentabilidad real ajustada por inflación.
- Progreso de objetivos.

## Consideraciones futuras

- Añadir cifrado.
- Añadir auditoría local.
- Añadir multi-currency serio.
- Añadir conciliación de movimientos.
- Añadir reglas de categorización.
- Añadir split transactions.
## Household bills

Tabla `household_bills` para seguimiento manual local de suministros y facturas del hogar.

Campos principales:

- `id`: UUID.
- `provider`: proveedor.
- `service_type`: `electricity`, `gas`, `water`, `internet`, `phone`, `home_insurance`, `rent_mortgage`, `community`.
- `period_start` / `period_end`: periodo de consumo.
- `amount` / `currency`: importe.
- `category_id`: categoria financiera asociada.
- `is_recurring`: si debe considerarse recurrente para planificacion.
- `due_date` / `paid_at`: vencimiento y pago.
- `notes`: observaciones manuales.

El resumen agrupa por proveedor y servicio, compara contra la factura anterior, marca subidas anomalas y estima el proximo recibo. La carga PDF/captura queda fuera del alcance inicial y se mantiene como evolucion futura local-first.
