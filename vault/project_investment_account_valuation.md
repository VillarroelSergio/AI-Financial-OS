---
name: Valoración calculada de cuentas de inversión
description: Las cuentas broker e investment separan efectivo y posiciones para evitar saldos artificiales y doble contabilización
metadata:
  type: project
---

Una cuenta `broker` o `investment` es un contenedor de posiciones, no un segundo activo.
Su valor actual se calcula como:

`total_value_eur = cash_balance_eur + portfolio_value_eur`

- `cash_balance_eur`: conversión a EUR de `current_balance`, interpretado como efectivo disponible.
- `portfolio_value_eur`: suma de `market_value` de sus holdings valorados.
- `position_count`: número de posiciones enlazadas, incluidas las pendientes de valorar.

El panel principal, el listado de cuentas y la herramienta `get_net_worth` de la IA usan
`build_current_valuation`, evitando que el saldo y las posiciones se cuenten dos veces.

Al añadir una acción o un fondo, el usuario debe seleccionar explícitamente una cartera
existente, crear una nueva en el mismo formulario o usar la cartera automática
`Sin cartera asignada`; nunca se elige la primera cartera por defecto. Al editar una posición
también se puede reasignar a otra cartera. El backend solo acepta cuentas activas de tipo
`broker` o `investment` para acciones y fondos. La
relación interna `Holding.account_id` se mantiene porque es necesaria para broker, divisa,
conciliación y agrupación, pero ya no obliga a navegar antes a Cuentas ni a introducir un
saldo total artificial de 0 €.

Las cuentas existentes conservan `current_balance`; en cuentas de inversión pasa a mostrarse
como efectivo disponible. Las posiciones nunca sobrescriben ese importe.

Las cuentas remuneradas son una excepción controlada: `Account(type=savings)` y el holding
`savings_account` representan el mismo saldo. El holding, que alimenta el motor de intereses,
prevalece como valoración actual y sustituye al `current_balance` en los agregados. Así se
incluyen las cuentas antiguas cuyo contenedor quedó a 0 € y se evita sumar dos veces las que
tienen el saldo replicado. Resumen, Balance General e IA reutilizan esta misma valoración.

En el módulo de Inversiones, ese saldo remunerado permanece dentro de `total_value` para
mostrar todo el valor gestionado, pero se excluye de `total_invested`, `return_absolute` y
`return_percent`. Es ahorro con intereses, no capital aportado a acciones o fondos, y no debe
diluir el P&L sobre aportado. Lo mismo aplica al asset técnico `cash`.

Relacionadas: [[project_investments_module]] · [[project_fund_reported_returns]] · [[04_DATA_MODEL]] · [[11_API_CONTRACT]]

Tags: #módulo #inversiones #cuentas #patrimonio #decisión
