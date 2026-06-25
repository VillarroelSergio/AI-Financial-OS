# UX Review Context — AI Financial OS

> Generated: 2026-06-24T07:08:07.548Z
> Viewport: 1440×900
> Data: mock (no datos reales de usuario)

## Cómo usar estas capturas

Estas capturas representan el estado visual actual de cada pantalla principal.
Úsalas para revisar el diseño, detectar regresiones visuales o dar contexto a agentes de IA
sin necesidad de arrancar la app ni tener datos reales.

Para regenerar: `npm run ux:snapshots` desde `apps/desktop/`.

## Pantallas capturadas

| Archivo | Pantalla | Estado | Descripción |
|---------|----------|--------|-------------|
| `markets.png` | Markets | mock_data | Market Watch con 36 activos en 8 categorías, tab Todos |
| `markets-europa.png` | Markets Europa | mock_data | Market Watch filtrado por categoría Europa |


## Notas para agentes

- Las pantallas `investments`, `goals`, `economy` e `insights` muestran estados vacíos
  porque aún no tienen implementación de datos en las fases actuales del roadmap.
- `imports-preview.png` requiere que el usuario suba un archivo CSV real; omitida en modo automático.
- Las métricas mostradas son ficticias (mock data) y sirven solo para verificar el layout.
