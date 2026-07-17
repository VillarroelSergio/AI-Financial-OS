# UX Review Context - AI Financial OS

> Generated: 2026-07-16T14:32:01.009Z
> Viewports: desktop 1440x900
> Data: mock (no datos reales de usuario)

## Como usar estas capturas

Estas capturas representan el estado visual actual de cada pantalla principal.
Usalas para revisar el diseno, detectar regresiones visuales o dar contexto a agentes de IA
sin necesidad de arrancar la app ni tener datos reales.

Para regenerar desktop: `npm run snapshots` desde `tools/ux-snapshot/`.
Para regenerar desktop/tablet/mobile: `npm run snapshots:responsive`.

## Pantallas capturadas

| Archivo | Pantalla | Viewport | Estado | Descripcion |
|---------|----------|----------|--------|-------------|
| `markets.png` | Markets | desktop | mock_data | Market Watch con 36 activos en 8 categorías, tab Todos |
| `markets-europa.png` | Markets Europa | desktop | mock_data | Market Watch filtrado por categoría Europa |


## Notas para agentes

- Las metricas mostradas son ficticias (mock data) y sirven solo para verificar el layout.
- Las pruebas responsive generan variantes desktop, tablet y mobile con el mismo contrato de rutas.
