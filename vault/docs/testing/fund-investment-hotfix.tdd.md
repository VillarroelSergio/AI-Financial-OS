# Hotfix de alta y rentabilidad de fondos — Evidencia TDD

## Origen y recorridos

Recorridos derivados de las capturas y del reporte del usuario:

1. Al crear un fondo con valor inicial, debe aparecer valorado inmediatamente en la tabla y en el resumen.
2. Si la plataforma informa ganancia absoluta y rentabilidad porcentual con bases distintas, ambas deben conservarse sin forzar una equivalencia matemática falsa.
3. Al añadir una valoración posterior, el último valor, aportado acumulado y porcentaje reportado deben alimentar la posición.

4. Al editar una posición desde la tabla, el formulario debe quedar visible en el viewport.
5. El total de Fondos debe ponderar la rentabilidad reportada por el capital aportado, sin sustituirla por el P&L simple.

## Evidencia RED / GREEN

| Garantía | Prueba | Tipo | RED | GREEN |
|---|---|---|---|---|
| El primer snapshot valora el holding en el alta | `test_create_fund_is_immediately_valued_in_holdings_and_summary` | Integración API | `market_value` devolvía `None` | PASS |
| El porcentaje de Finizens se conserva en el snapshot | `test_fund_snapshot_preserves_platform_reported_return` | Integración API | faltaba `reported_return_pct` | PASS |
| Una valoración posterior sincroniza valor, coste y porcentaje | `test_fund_snapshot_preserves_platform_reported_return` | Integración API | comportamiento no soportado | PASS |
| El total de fondos pondera los porcentajes externos | `test_fund_summary_weights_platform_returns_by_contributed_capital` | Integración API | faltaba `fund_reported_return_percent` | PASS |

Comando RED/GREEN focalizado:

```text
uv run pytest app/tests/test_investments.py -k "create_fund_is_immediately_valued or fund_snapshot_preserves_platform_reported_return" -q
```

- RED: 2 fallos por `market_value = None` y ausencia de `reported_return_pct`.
- GREEN: 2 pruebas correctas, 26 deseleccionadas.

## Verificación adicional

- `uv run pytest app/tests/test_investments.py -q`: 26 correctas y 2 fallos preexistentes no relacionados (`needs_manual_nav` y conciliación de una cuenta de ahorro).
- `npm run build`: TypeScript y build de producción correctos.
- `npm run ux:snapshots:headed`: 21/21 capturas generadas.
- QA focalizada del modal con 997,06 €, +264,66 € y 58,05 %: el formulario deriva 732,40 € aportados, conserva el porcentaje reportado y cabe completo en viewport de escritorio.
- QA de interacción de `Editar`: el editor queda visible y centrado dentro de una capa modal fija de 1280 × 692 px en un viewport de 1280 × 720 px.
- Caso Finizens de dos planes: 34,38 % ponderado por 5.400 € y 28,02 % por 4.800 € produce aproximadamente 31,39 % reportado total.
- La tarjeta de Fondos etiqueta el agregado como `reportada`; el KPI global mantiene la etiqueta `P&L sobre aportado`.

## Cobertura y límites

No se ejecutó un informe porcentual de cobertura global. El hotfix queda cubierto por tres pruebas de integración que atraviesan alta de cuenta, alta de fondo, snapshots, listado de holdings y resumen. Los dos fallos preexistentes de la suite se mantienen fuera del alcance de esta corrección.
