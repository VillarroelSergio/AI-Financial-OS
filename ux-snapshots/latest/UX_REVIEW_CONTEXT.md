# UX Review Context - AI Financial OS

> Generated: 2026-07-03T13:12:49.160Z
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
| `welcome.png` | Welcome | desktop | mock_data | Guía inicial de bienvenida con pasos de carga de datos |
| `investments-tracking.png` | Position Tracking | desktop | mock_data | Seguimiento de posiciones: evolución de cada acción desde el precio de entrada |
| `overview.png` | Overview | desktop | mock_data | Dashboard principal con patrimonio neto, liquidez, inversiones y métricas del mes |
| `spending.png` | Spending | desktop | mock_data | Análisis de gastos mensual con pie chart por categoría y desglose |
| `investments.png` | Investments | desktop | mock_data | Portfolio tracker con TR stocks, Finizens funds y cuenta remunerada |
| `investments-quality.png` | Investments Quality | desktop | mock_data | Calidad de cartera con confianza, precios, FX y posiciones manuales |
| `investments-empty.png` | Investments (empty) | desktop | empty | Estado vacío sin posiciones registradas |
| `goals.png` | Goals | desktop | empty | Objetivos financieros — estado inicial sin objetivos |
| `economy.png` | Economy | desktop | empty | Indicadores macroeconómicos — estado inicial |
| `insights.png` | Insights | desktop | empty | Insights personalizados — estado inicial sin análisis |
| `imports-empty.png` | Imports (empty) | desktop | empty | Centro de importación — estado vacío antes de seleccionar archivo |
| `imports-preview.png` | Imports (preview) | desktop | preview_demo | Centro de importación — preview y validación con datos ficticios |
| `settings.png` | Settings | desktop | mock_data | Configuración de la aplicación — idioma, moneda y tema |
| `markets.png` | Markets | desktop | mock_data | Market Watch con 36 activos en 8 categorías, tab Todos |
| `markets-europa.png` | Markets Europa | desktop | mock_data | Market Watch filtrado por categoría Europa |
| `planificacion.png` | Planificacion | desktop | mock_data | Planificacion con presupuestos, recurrentes asistidos y cashflow |
| `planificacion-recurrentes.png` | Planificacion Recurrentes | desktop | mock_data | Deteccion asistida de recurrentes con candidatos confirmables |
| `planificacion-facturas.png` | Planificacion Facturas | desktop | mock_data | Facturas del hogar con comparativa, anomalias y proximo recibo |
| `transactions.png` | Transactions | desktop | mock_data | Ledger con busqueda, filtros, nombres legibles y acciones seguras |
| `assistant.png` | Assistant | desktop | provider_offline | Copiloto IA contextual con provider local no disponible |
| `portfolio-import.png` | Portfolio Import | desktop | empty | Importacion de cartera con capturas, texto fallback y entrada manual |


## Notas para agentes

- Las metricas mostradas son ficticias (mock data) y sirven solo para verificar el layout.
- Las pruebas responsive generan variantes desktop, tablet y mobile con el mismo contrato de rutas.
