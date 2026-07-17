# E2E report — FLOW-01..33

Generated: 2026-07-16T13:43:57.717Z
Base URL: http://localhost:1420
API URL: http://127.0.0.1:18010
Isolated data directory: C:\Users\SERGIO~1\AppData\Local\Temp\ai-financial-os-e2e\flow-01-05-1784209427543

## Flows

| Flow | Status | Reason |
|---|---|---|
| FLOW-01 | PASS |  |
| FLOW-02 | PASS |  |
| FLOW-03 | PASS |  |
| FLOW-04 | PASS |  |
| FLOW-05 | PASS |  |
| FLOW-06 | PASS |  |
| FLOW-07 | PASS |  |
| FLOW-08 | PASS |  |
| FLOW-09 | PASS |  |
| FLOW-10 | BLOCKED | El histórico efímero no contiene las ocurrencias mínimas. |
| FLOW-11 | PASS |  |
| FLOW-12 | PASS |  |
| FLOW-13 | BLOCKED | Pendiente de provider/fixture externo; separado del piloto determinista. |
| FLOW-14 | BLOCKED | Pendiente de provider/fixture externo; separado del piloto determinista. |
| FLOW-15 | BLOCKED | Pendiente de provider/fixture externo; separado del piloto determinista. |
| FLOW-27 | BLOCKED | Pendiente de provider/fixture externo; separado del piloto determinista. |
| FLOW-28 | BLOCKED | Pendiente de provider/fixture externo; separado del piloto determinista. |
| FLOW-29 | BLOCKED | Pendiente de provider/fixture externo; separado del piloto determinista. |
| FLOW-16 | PASS |  |
| FLOW-17 | PASS |  |
| FLOW-18 | PASS |  |
| FLOW-19 | PASS |  |
| FLOW-20 | PASS |  |
| FLOW-21 | PASS |  |
| FLOW-22 | PASS |  |
| FLOW-23 | PASS |  |
| FLOW-24 | PASS |  |
| FLOW-25 | PASS |  |
| FLOW-26 | PASS |  |
| FLOW-30 | PASS |  |
| FLOW-31 | PASS |  |
| FLOW-32 | PASS |  |
| FLOW-33 | PASS |  |

## Console errors

- None

## HTTP 5xx responses

- None

## Findings

- FLOW-05 valida la semántica actual: el saldo inicial de la cuenta suma +1000 € al patrimonio y los movimientos alimentan los agregados mensuales (+500 € ingresos y 42,30 € gasto). FLOW-17..22 usan fixtures locales de Playwright; inversiones, RAG e IA siguen BLOCKED hasta disponer de sus adaptadores deterministas.