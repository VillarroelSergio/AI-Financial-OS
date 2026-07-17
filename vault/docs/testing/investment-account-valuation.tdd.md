# Cuentas de inversión calculadas — Evidencia TDD

## Recorridos

1. Una cuenta de inversión muestra por separado efectivo, posiciones y total.
2. El patrimonio suma cada importe una sola vez.
3. Cuentas, panel principal e IA devuelven el mismo total.
4. El alta de una acción o fondo permite crear o asignar una cartera sin salir del formulario.
5. Una posición existente puede cambiar de cartera, pero no moverse a una cuenta bancaria.
6. Las altas nuevas exigen elegir cartera y no toman automáticamente la primera disponible.

## Evidencia RED / GREEN

| Garantía | Prueba | RED | GREEN |
|---|---|---|---|
| 100 € de efectivo + 1.500 € en posiciones producen 1.600 € | `test_investment_account_derives_total_from_cash_and_positions_once` | la API no exponía valores derivados | PASS |
| Panel e IA usan esos mismos 1.600 € | misma prueba de integración | IA ignoraba holdings | PASS |
| Reasignar una acción actualiza `account_id` y broker; una cuenta bancaria se rechaza | `test_holding_can_be_reassigned_only_to_an_investment_portfolio` | `PATCH` ignoraba `account_id` | PASS |
| Una remunerada enlazada a una cuenta a 0 € entra en Resumen | `test_overview_uses_savings_holding_when_container_balance_is_zero` | Resumen no normalizaba la doble representación | PASS |
| Una remunerada nueva no se cuenta dos veces | `test_overview_counts_new_savings_account_only_once` | Cuenta y holding contenían el mismo saldo | PASS |
| El ahorro remunerado suma al valor total pero no al P&L sobre aportado | `test_summary_excludes_remunerated_savings_from_investment_pnl` | Los 19.000 € de ahorro diluían el porcentaje global | PASS |

## Verificación

- Prueba focalizada: 1 correcta.
- Regresión de cuentas/panel/IA: 6 correctas.
- Regresión completa del backend (2026-07-16): 450 correctas; los antiguos fallos de `needs_manual_nav` y conciliación de ahorro eran fixtures desalineados y ya están corregidos.
- `npm run build`: correcto.
- `npm run ux:snapshots:headed`: 21/21 capturas.
- QA de interacción: el modal ofrece cartera existente, `+ Nueva cartera` y `Usar sin asignar`; el formulario integrado es visible y cabe en el modal.
- Los casos de cuentas remuneradas y exclusión del ahorro del P&L pasaron dentro de la suite completa autorizada el 16/07/2026.

No se ejecutó cobertura porcentual global. La prueba nueva atraviesa alta de cuenta, activo,
holding, listado de cuentas, resumen del panel y herramienta de IA.
