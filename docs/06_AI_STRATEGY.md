# 06 — AI Strategy

## Objetivo

Integrar IA local para explicar, comparar y contextualizar datos financieros sin comprometer privacidad ni delegar cálculos críticos en el modelo.

## Providers

La arquitectura debe soportar:

- Ollama.
- LM Studio.

Modelo inicial recomendado:

- Qwen.

## Principios

- La IA se ejecuta localmente.
- La IA no accede directamente a SQLite.
- La IA usa tools controladas.
- La IA no calcula patrimonio, rentabilidad o ahorro desde texto libre.
- La IA explica datos calculados por servicios deterministas.
- La IA debe mostrar de qué datos parte.
- La IA nunca debe dar asesoramiento financiero vinculante.

## Arquitectura

```txt
AI Panel
 → AI Service
 → Provider Adapter
   ├─ Ollama Adapter
   └─ LM Studio Adapter
 → Tool Router
 → Domain Services
 → Structured Result
 → LLM Explanation
```

## Provider interface

```txt
generate(prompt, context, tools)
stream(prompt, context, tools)
list_models()
healthcheck()
```

## Tools iniciales

### Finanzas personales

```txt
get_net_worth()
get_monthly_summary(month)
get_spending_by_category(month)
compare_periods(period_a, period_b)
get_savings_rate(month)
get_recent_transactions(filters)
get_account_balances()
```

### Inversiones

```txt
get_investment_summary()
get_asset_allocation()
get_holdings()
get_investment_performance(period)
```

### Mercado y economía

```txt
get_market_snapshot()
get_macro_snapshot(region)
get_indicator_latest(code, region)
get_indicator_history(code, region, start_date, end_date)
```

### Objetivos

```txt
get_goals()
get_goal_progress(goal_id)
simulate_goal(goal_id, monthly_contribution)
simulate_monthly_investment(amount, years, expected_return)
```

## Tipos de interacción

### Insight contextual

Pequeñas tarjetas generadas por reglas o IA.

Ejemplo:

> Tu gasto en ocio está por encima de tu media de los últimos meses.

### Ask AI

Botón contextual en cada módulo.

Ejemplo:

- Preguntar sobre estos gastos.
- Explicar esta variación.
- Comparar con el mes anterior.

### Panel lateral

El chat no debe ocupar la app completa. Debe aparecer como panel lateral para mantener el contexto visual.

## Prompt system base

```txt
Eres un analista financiero personal integrado en una aplicación local-first.
Tu función es explicar datos del usuario de forma clara, prudente y accionable.
No inventes cifras.
No des recomendaciones de inversión específicas.
No afirmes que eres asesor financiero.
Usa solo los datos proporcionados por las tools.
Si los datos son insuficientes, dilo claramente.
Responde en español.
```

## Estilo de respuesta

Cada respuesta debe intentar seguir:

```txt
Qué ocurre
Por qué importa
Qué datos lo explican
Qué opciones tiene el usuario
```

## Guardrails

La IA debe evitar:

- “Compra X acción”.
- “Vende Y fondo”.
- “Esta inversión es segura”.
- “Garantizado”.
- “Deberías hacer…”.

Preferir:

- “Podrías valorar…”.
- “Según tus datos…”.
- “Este escenario sugiere…”.
- “Con la información disponible…”.

## Trazabilidad

Cada respuesta importante debe incluir metadatos internos:

```txt
tools_used
data_period
confidence_level
missing_data
```

La UI puede mostrarlo como “Datos usados”.

## Fases IA

### IA V1

- Provider abstraction.
- Healthcheck Ollama/LM Studio.
- Chat lateral.
- Tools básicas de lectura.

### IA V2

- Resúmenes mensuales.
- Comparativas.
- Insights redactados.

### IA V3

- Simulaciones.
- Impacto de inflación.
- Contexto macro.

### IA V4

- RAG documental.
- Preguntas sobre PDFs.

## Fase 6.1 - Estabilizacion

La IA local no consulta Internet, no accede directamente a SQLite y no ejecuta SQL libre.
Las tools consumen solo capas vigentes:

- Market Intelligence: `get_market_snapshot`, `get_macro_snapshot`, `get_forex_snapshot`, `get_bond_snapshot`, `get_provider_quality`.
- Financial Knowledge: `get_market_regime`, `get_financial_signals`, `get_personal_impact_summary`, `get_ai_datasheet`.
- Finanzas personales: `get_net_worth`, `get_monthly_summary`, `get_spending_by_category`, `compare_periods`, `get_savings_rate`, `get_goal_progress`.

No se permite que `backend/app/modules/ai/tools` dependa de `economic_data` ni `market_data` legacy.

Todas las tools devuelven:

```json
{
  "ok": true,
  "tool": "get_macro_snapshot",
  "data": {},
  "sources": [],
  "quality_score": 0.94,
  "warnings": []
}
```

En error, `ok=false`, `data=null`, `quality_score=0` y `error` contiene el detalle tecnico.
La respuesta del chat conserva `tool_calls`, `sources` y `quality_score`; el frontend puede mostrarlo como "Ver datos usados".

Pruebas locales:

- Ollama: iniciar `ollama serve`, descargar el modelo configurado y consultar `GET /api/ai/status`.
- LM Studio: arrancar el servidor OpenAI-compatible y consultar `GET /api/ai/providers`.
- Chat: usar `POST /api/ai/chat` con preguntas macro, mercado, finanzas personales y "Que datos has usado?".
