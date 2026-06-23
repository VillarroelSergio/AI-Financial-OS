# 14 — Implementation Prompts

## Prompt maestro para Claude Code

```txt
Asume el rol de un ingeniero senior experto en arquitectura desktop, React, Tauri, Python, FastAPI, SQLite, DuckDB, UX/UI y aplicaciones local-first.

Vas a implementar el proyecto AI Financial OS en Visual Studio Code.

Antes de escribir código, lee toda la documentación del directorio /docs, especialmente:
- 00_PROJECT_BRIEF.md
- 02_ROADMAP.md
- 03_ARCHITECTURE.md
- 04_DATA_MODEL.md
- 05_IMPORT_STRATEGY.md
- 08_UX_UI_GUIDELINES.md
- 09_DESIGN_SYSTEM.md
- 10_SECURITY_MODEL.md
- 11_API_CONTRACT.md
- 13_CLAUDE_CODE_GUIDE.md

Restricciones obligatorias:
- No implementar automatización bancaria.
- No implementar scraping.
- No leer email.
- No usar cloud para datos personales.
- No implementar IA antes de que el core financiero esté preparado.
- No permitir que el LLM consulte SQL directamente.
- No sobrecargar la UI.
- Mantener estilo Dark Premium.
- Mantener idioma español.

Stack obligatorio:
- Tauri
- React
- TypeScript
- Tailwind
- shadcn/ui
- Recharts
- Python
- FastAPI
- SQLite
- DuckDB
- Preparado para Ollama y LM Studio

Implementa solo la fase indicada por el usuario. Si detectas que una tarea pertenece a una fase posterior, indícalo y propón dejarlo preparado sin implementarlo.

Al finalizar cada bloque, entrega:
1. Resumen de implementación.
2. Archivos creados/modificados.
3. Cómo ejecutar y probar.
4. Decisiones tomadas.
5. Pendientes.
```

## Prompt Fase 0 — Foundation

```txt
Implementa la Fase 0 del proyecto AI Financial OS.

Objetivo:
Crear la base técnica del monorepo con Tauri + React + TypeScript en frontend y FastAPI + SQLite + DuckDB en backend.

Incluye:
- Estructura de carpetas según docs/03_ARCHITECTURE.md.
- App Tauri funcional.
- React con routing base.
- Tailwind configurado.
- shadcn/ui preparado.
- Layout base con sidebar y topbar.
- Tema Dark Premium inicial.
- Backend FastAPI con endpoint /health.
- Configuración inicial de SQLite.
- Configuración inicial de DuckDB.
- Scripts para levantar frontend y backend.
- README con instrucciones de desarrollo.

No incluyas:
- IA.
- Importadores.
- RAG.
- APIs bancarias.
- Automatización.

Cuida especialmente la calidad visual inicial y los estados vacíos.
```

## Prompt Fase 1 — Financial Core

```txt
Implementa la Fase 1: Financial Core MVP.

Objetivo:
Permitir crear cuentas, categorías y movimientos manuales, y visualizar un dashboard financiero básico.

Incluye backend:
- Modelos Account, Category y Transaction.
- Migración o creación de tablas.
- Repositories/services/routes.
- Endpoints definidos en docs/11_API_CONTRACT.md.
- Cálculo de overview financiero.

Incluye frontend:
- Pantalla Overview.
- Pantalla Accounts.
- Pantalla Transactions.
- Pantalla Spending básica.
- Componentes MetricCard, ChartCard y EmptyState.
- Formularios simples para crear cuentas y movimientos.

No incluyas:
- IA.
- Importación CSV.
- Market/Economy.
- Inversiones avanzadas.

La UI debe ser Dark Premium, limpia y no sobrecargada.
```

## Prompt Fase 2 — Import Center + Monefy

```txt
Implementa la Fase 2: Import Center con soporte para Monefy CSV.

Objetivo:
Permitir importar manualmente un CSV de Monefy, previsualizarlo, validarlo, confirmar la importación y actualizar los dashboards.

Usa como referencia docs/05_IMPORT_STRATEGY.md.

Columnas esperadas de Monefy:
- date
- account
- category
- amount
- currency
- converted amount
- currency.1
- description

Incluye backend:
- ImportBatch.
- ImportRow.
- Parser de Monefy.
- Normalización de fecha D/M/YYYY a ISO.
- Validaciones.
- Detección básica de duplicados.
- Confirmación de importación.
- Rollback.

Incluye frontend:
- Pantalla Imports.
- Stepper: Fuente → Archivo → Preview → Validación → Confirmación → Resumen.
- Tabla de preview.
- Estados de error y advertencia.
- Confirmación explícita antes de guardar.

Restricciones:
- No enviar datos a IA.
- No automatizar la carga.
- No subir archivos a terceros.
```

## Prompt Fase 3 — Investments Basic

```txt
Implementa la Fase 3: Investments Basic.

Objetivo:
Permitir registrar manualmente inversiones de Trade Republic, Finizens y cuentas remuneradas.

Incluye:
- InvestmentAsset.
- Holding.
- InvestmentOperation básica.
- Pantalla Investments.
- Resumen de valor total.
- Distribución por activo.
- Rentabilidad simple.
- Formularios de alta manual.

No incluyas importación automática de brokers ni scraping.
```

## Prompt Fase 4 — Market Watch

```txt
Implementa la Fase 4: Market Watch.

Objetivo:
Añadir datos de mercado consultables online y cacheados localmente.

Incluye:
- MarketInstrument.
- MarketObservation.
- Servicio provider abstracto.
- Refresh manual.
- Vista Market Watch integrada en Economy o sección propia.
- Última actualización visible.

Instrumentos iniciales:
- IBEX 35
- Euro Stoxx 50
- STOXX Europe 600
- S&P 500
- Nasdaq 100
- Dow Jones
- MSCI World
- EUR/USD
- Bono España 10Y
- Bund 10Y
- Treasury 10Y

No mezcles datos personales con llamadas externas.
```

## Prompt Fase 5 — Economic Intelligence

```txt
Implementa la Fase 5: Economic Intelligence.

Objetivo:
Añadir indicadores macroeconómicos de España, Eurozona y EEUU con caché local y UI limpia.

Incluye:
- EconomicIndicator.
- EconomicObservation.
- Providers abstractos.
- Snapshot económico.
- Vista por región.
- Vista de inflación, empleo, PIB y tipos.
- Comparativas simples España/Eurozona/EEUU.

Indicadores:
- Inflación.
- Inflación subyacente.
- Paro.
- PIB.
- Tipos BCE/FED.
- Euríbor.
- Bonos 10 años.
- Índices.
- Divisas.

No incluyas materias primas ni noticias.
```

## Prompt Fase 6 — Local AI Assistant

```txt
Implementa la Fase 6: Local AI Assistant.

Objetivo:
Integrar Ollama y LM Studio mediante una abstracción multi-provider y un panel lateral de IA.

Incluye:
- AI provider interface.
- Ollama adapter.
- LM Studio adapter.
- Healthcheck.
- Configuración de modelo Qwen.
- AI side panel.
- Tool router.
- Tools financieras básicas.
- Respuestas basadas en datos calculados por backend.

Restricciones:
- El LLM no puede consultar SQL directamente.
- No inventar cifras.
- Mostrar datos usados.
- No dar recomendaciones de inversión específicas.
```
