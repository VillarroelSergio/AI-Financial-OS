# UX Review Context — AI Financial OS

> Generated: 2026-06-23T13:49:08.767Z
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
| `investments.png` | Investments | empty | Cartera de inversiones — estado inicial sin datos |
| `goals.png` | Goals | empty | Objetivos financieros — estado inicial sin objetivos |
| `economy.png` | Economy | empty | Indicadores macroeconómicos — estado inicial |
| `insights.png` | Insights | empty | Insights personalizados — estado inicial sin análisis |
| `imports-empty.png` | Imports (empty) | empty | Centro de importación — estado vacío antes de seleccionar archivo |
| `settings.png` | Settings | mock_data | Configuración de la aplicación — idioma, moneda y tema |

## Capturas omitidas (requieren interacción manual)

- **imports-preview.png**: requires manual file upload interaction

## Notas para agentes

- Las pantallas `investments`, `goals`, `economy` e `insights` muestran estados vacíos
  porque aún no tienen implementación de datos en las fases actuales del roadmap.
- `imports-preview.png` requiere que el usuario suba un archivo CSV real; omitida en modo automático.
- Las métricas mostradas son ficticias (mock data) y sirven solo para verificar el layout.
