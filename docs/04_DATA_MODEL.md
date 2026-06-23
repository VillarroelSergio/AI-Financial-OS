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
