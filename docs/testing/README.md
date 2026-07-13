# Contratos de prueba end-to-end

`flows/catalog.yaml` es la fuente de verdad de los 33 recorridos de usuario de
Financial OS. Cada FLOW define precondiciones, pasos visibles, aserciones, limpieza y
el escenario sintético que lo alimenta.

`fixtures/financial-os.yaml` contiene exclusivamente datos sintéticos. Los runners
deben utilizar una base efímera local y no pueden escribir en datos de usuario ni
consultar proveedores externos durante la suite determinista.

## Validación

Desde `tools/ux-snapshot`:

```powershell
npm run test:flows
npm run e2e:flow-01-33
npm run e2e:flow-01-33:headed
```

El runner valida el catálogo antes de iniciar backend, frontend o navegador. Un FLOW
sin pasos, aserciones o fixture determinista detiene la ejecución.

## Capas de prueba

- **Contrato de flujo:** valida la cobertura y estructura de los recorridos.
- **E2E determinista:** usa UI real, backend local y fixtures locales.
- **API e invariantes financieras:** cubre reglas de dominio, importes, signos y
  persistencia.
- **Smoke externo:** se añadirá como suite independiente para proveedores reales;
  nunca bloquea la suite determinista.
