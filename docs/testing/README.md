# Pruebas end-to-end (E2E)

Esta carpeta define y documenta la suite E2E de Financial OS. La suite recorre la aplicación web con Playwright, arranca un backend local aislado y genera evidencia para cada flujo ejecutado.

## Objetivos y límites

- Validar recorridos de usuario, resultados visibles, API, consola e invariantes financieras.
- No utilizar datos personales, la base local del usuario ni proveedores reales.
- No dejar procesos en `1420` y `18010` ni bases de datos dentro del repositorio.
- Mercados y Economía usan fixtures locales de Playwright. Inversiones, RAG e IA permanecen `BLOCKED` hasta contar con adaptadores deterministas.

## Estructura

| Ruta | Responsabilidad |
|---|---|
| `flows/catalog.yaml` | Fuente de verdad de FLOW-01 a FLOW-33: precondiciones, pasos, aserciones y limpieza. |
| `fixtures/financial-os.yaml` | Datos sintéticos y política de aislamiento. |
| `tools/ux-snapshot/run-flow-01-05.ts` | Runner Playwright de la suite. |
| `tools/ux-snapshot/flow-contracts.ts` | Cargador y validador de contratos YAML. |
| `ux-snapshots/e2e/flow-01-05/` | Informe y capturas de la última ejecución; son artefactos generados. |

## Requisitos

- Node.js y dependencias de `tools/ux-snapshot` instaladas.
- Entorno Python en `backend/.venv`.
- Puertos `1420` y `18010` libres. El runner se detiene antes de escribir datos si alguno está ocupado.

## Comandos

Ejecutar desde `D:\FinancialAgent\AI-Financial-OS\tools\ux-snapshot`:

```powershell
# Valida los 33 contratos: pasos, aserciones y fixtures.
npm run test:flows

# Comprueba que las bases E2E nunca se creen dentro del repositorio.
npm run test:e2e-isolation

# Ejecuta la suite sin mostrar el navegador.
npm run e2e:flow-01-33

# Ejecuta la misma suite mostrando Chromium.
npm run e2e:flow-01-33:headed
```

Los alias `e2e:flow-01-05` y `e2e:flow-01-05:headed` se conservan por compatibilidad, pero apuntan al runner actual; no deben usarse para asumir que solo se ejecutan cinco flujos.

### Ejecución visible más lenta

El modo `headed` aplica por defecto 1200 ms entre FLOWs, 70 ms por carácter y `slowMo` de Playwright. Para observar cada acción con más calma:

```powershell
$env:E2E_ACTION_DELAY_MS = "2000"
$env:E2E_TYPE_DELAY_MS = "120"
npm run e2e:flow-01-33:headed
```

Para volver al valor por defecto, abre una terminal nueva o ejecuta:

```powershell
Remove-Item Env:E2E_ACTION_DELAY_MS
Remove-Item Env:E2E_TYPE_DELAY_MS
```

## Aislamiento y limpieza

Cada ejecución crea SQLite, DuckDB y Market Intelligence en:

```text
%TEMP%\ai-financial-os-e2e\flow-01-05-<timestamp>
```

Nunca en `AI-Financial-OS\.e2e-data`. Al finalizar, el runner cierra Chromium, backend y Vite, espera a que `1420` y `18010` estén libres y borra el directorio temporal. `.e2e-data/` está ignorado por Git como protección adicional para restos manuales de versiones antiguas.

Si una ejecución se interrumpe externamente, se puede borrar únicamente `flow-01-05-*` dentro de `%TEMP%\ai-financial-os-e2e` después de comprobar que no hay procesos E2E en marcha.

## Resultados y estados

El informe queda en `ux-snapshots/e2e/flow-01-05/report.md`.

- `PASS`: el recorrido y sus aserciones finalizaron.
- `FAIL`: discrepancia de producto, UI, API, red o consola.
- `BLOCKED`: requiere un fixture/adaptador pendiente; nunca equivale a aprobado.

La suite actual ejecuta FLOW-01..12, FLOW-16..26 y FLOW-30..33. FLOW-10 puede quedar `BLOCKED` si no hay histórico suficiente. FLOW-13..15 y FLOW-27..29 siguen pendientes de fixtures deterministas.

## Cómo ampliar la suite

1. Actualiza `flows/catalog.yaml` con el contrato observable.
2. Añade o ajusta los datos sintéticos en `fixtures/financial-os.yaml`.
3. Implementa la interacción y las aserciones en el runner.
4. Ejecuta `npm run test:flows`, `npm run test:e2e-isolation` y la suite E2E.
5. No añadas proveedores reales a la suite determinista; para ellos debe existir un smoke test externo independiente.
