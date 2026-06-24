# UX Review Context — AI Financial OS

> Generated: 2026-06-24T19:26:15.849Z
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
| `overview.png` | Overview | mock_data | Dashboard principal con patrimonio neto, liquidez, inversiones y métricas del mes |
| `spending.png` | Spending | mock_data | Análisis de gastos mensual con pie chart por categoría y desglose |
| `investments.png` | Investments | mock_data | Portfolio tracker con TR stocks, Finizens funds y cuenta remunerada |
| `investments-empty.png` | Investments (empty) | empty | Estado vacío sin posiciones registradas |
| `goals.png` | Goals | empty | Objetivos financieros — estado inicial sin objetivos |
| `economy.png` | Economy | empty | Indicadores macroeconómicos — estado inicial |
| `insights.png` | Insights | empty | Insights personalizados — estado inicial sin análisis |
| `imports-empty.png` | Imports (empty) | empty | Centro de importación — estado vacío antes de seleccionar archivo |
| `imports-preview.png` | Imports (preview) | preview_demo | Centro de importación — preview y validación con datos ficticios |
| `settings.png` | Settings | mock_data | Configuración de la aplicación — idioma, moneda y tema |
| `markets.png` | Markets | mock_data | Market Watch con 36 activos en 8 categorías, tab Todos |
| `markets-europa.png` | Markets Europa | mock_data | Market Watch filtrado por categoría Europa |


## Notas para agentes

- Las pantallas `investments`, `goals`, `economy` e `insights` muestran estados vacíos
  porque aún no tienen implementación de datos en las fases actuales del roadmap.
- `imports-preview.png` requiere que el usuario suba un archivo CSV real; omitida en modo automático.
- Las métricas mostradas son ficticias (mock data) y sirven solo para verificar el layout.
