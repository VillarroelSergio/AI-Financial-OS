# GitHub Actions — contratos del backend

## Origen y alcance

El job `Backend · Ruff y Pytest` del PR #36 detectó ocho expectativas que habían
quedado desalineadas respecto a los contratos actuales. La corrección actualiza
exclusivamente pruebas; no modifica código de producción.

## Evidencia RED / GREEN

| Garantía | Prueba | RED observado | GREEN |
|---|---|---|---|
| Un fondo manual con ticker puede refrescarse sin depender del buscador | `test_refresh_fetches_price_for_manual_assets_with_ticker` | faltaba `price_source` al intentar crear una acción no resoluble | PASS |
| El ahorro remunerado suma en liquidez e inversiones sin duplicar patrimonio | `test_overview_converts_fx_and_includes_portfolio` | esperaba 1.500 € en vez de 5.500 € | PASS |
| `/health` publica la versión vigente de la API | `test_health_returns_ok` | esperaba `0.1.0` en vez de `1.0.0` | PASS |
| Un fondo realmente manual y sin ticker solicita NAV | `test_price_refresh_marks_manual_assets` | el nombre usado se autorresolvía a un ticker | PASS |
| Las remuneradas quedan fuera de Calidad de cartera | `test_reconciliation_classifies_funds_manual_savings_confirmed` | esperaba una remunerada deliberadamente excluida | PASS |
| SpaceX permanece ambiguo aunque el proveedor devuelva más candidatos | `test_resolve_spacex` | exigía exactamente un candidato | PASS |
| La reasignación de divisa actúa sobre movimientos USD reales | `test_currency_reassign_preview_and_apply` | Monefy normaliza deliberadamente a EUR | PASS |
| Una serie de 60 días ofrece `1d`, `5d`, `1m` y `max` | `test_available_ranges_honest_with_short_series` | omitía las ventanas cortas disponibles | PASS |

## Verificación

- RED remoto y local: `8 failed, 442 passed`.
- GREEN focalizado: `8 passed, 1 warning in 2.96s`.
- GREEN completo: `450 passed, 1 warning in 87.72s`.
- Calidad: `uv run --frozen ruff check .` → `All checks passed!`.
- Advertencia conocida: deprecación de `httpx` en `starlette.testclient`; no afecta al resultado.

No se generó un informe porcentual de cobertura porque no cambió lógica de producción y
la suite completa de integración ya recorrió los 450 casos existentes.
