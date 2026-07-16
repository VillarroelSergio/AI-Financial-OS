---
name: project_ai_module_plan
description: "Estado del plan de mejora del módulo IA (PROPUESTA_ASISTENTE_IA v1/v2) — AI-1 core hecho, AI-2/3/4/5 pendientes"
metadata: 
  node_type: memory
  type: project
  originSessionId: a6d6f17b-07c4-4524-b2dc-8c4a0332dbd7
---

# Plan mejora Módulo IA (docs/PROPUESTA_ASISTENTE_IA.md + _V2.md)

Guía: V2 define sprints AI-0..AI-5. Prioridad de docs: Fase0+1+2 primero ("80% del dolor visible").

**HECHO (2026-07-12, sin commit) — tranche AI-1 core + deuda visible:**
- Renderer Markdown restringido: `apps/desktop/src/features/assistant/components/Markdown.tsx` (React elements, sin dangerouslySetInnerHTML → sin XSS, sin dependencia). Wired en AiMessageList (P1 resuelto).
- System prompt v2 con contrato de salida: prohíbe tablas/emojis/`***`, headings ≤h4, estructura prosa "qué ocurre/por qué importa/qué datos/qué opciones" (system_prompt.py).
- Guardrail determinista `prompts/guardrails.py` `sanitize_response()`: strip emojis + HR separators + normaliza whitespace. Con self-check `__main__`. Wired en service.py antes de persistir.
- Fixes deuda visible: timeout cliente 90s→130s (>120s provider), hint offline provider-aware (LM Studio vs Ollama), `insight_id` añadido al filtro de contexto seguro.
- Verificado: tsc --noEmit exit 0, guardrail self-check ok, AST parse backend ok. NO se corrieron pytest ni ux:snapshots (requieren stack+LLM; pendiente correr ux:snapshots:headed con app arriba).

**HECHO (2026-07-12, sin commit) — AI-3 núcleo (Centro de Análisis):**
- Modelo `AiBrief` (tabla `ai_briefs`) en app/models/ai.py; registrada en models/__init__.
- `backend/app/modules/ai/analysis.py`: orchestrator determinista (`SCOPES={monthly_review}`, reutiliza `insights_service.get_monthly_review` — NO segunda fuente de verdad), `build_bundle`, redactor LLM `render_narrative` (1 llamada, sin tools) con fallback `_deterministic_narrative`, repo idempotente DELETE+INSERT (`generate_brief`/`list_briefs`/`get_brief`). El brief nunca bloquea.
- Rutas: `POST /api/ai/briefs`, `GET /api/ai/briefs`, `GET /api/ai/briefs/{scope}/{period}`. Schemas `BriefGenerateRequest`/`BriefOut`.
- Frontend: `AnalysisCenter.tsx` (hero brief + key figures + narrativa Markdown + señales + acciones deep-link `navigate(target)` + historial + trace badge), hook `useBriefs`, api `listBriefs`/`generateBrief`, tipos. `AssistantPage` reconvertida a 2 pestañas: **Análisis** (default) + **Chat** (contenido previo intacto).
- Verificado: tsc exit 0; backend import+rutas+tabla OK; self-check funciones puras OK; test `app/tests/test_ai_briefs.py` (fallback+idempotencia) compila (NO ejecutado, usuario correrá pytest).

**HECHO (2026-07-12, sin commit) — AI-1 `structured` en el chat:**
- Clave de la doc (V2 línea 54): `key_figures`/`actions` vienen de las TOOLS, no del texto del LLM (determinista, no JSON-schema del modelo). `service._harvest_structured(all_tool_calls)` extrae de los resultados de tool las formas ya tipadas `InsightMetricOut` ({label,value,unit,precision}) y `InsightActionOut` ({label,target,params}) — top-level `primary_metric`/`actions` + `insights[].primary_metric`/`insights[].actions`; dedupe por label / (label,target); tope 6 figs / 5 acciones.
- Schemas `StructuredFigure`/`StructuredAction`/`StructuredPayload` + campo `structured` en `ChatResponse`. Frontend: tipos `AiStructuredFigure`/`AiStructured`, `structured` en LocalMessage, `StructuredPanel` en AiMessageList (chips de cifras con formato local + botones deep-link `navigate(target)`). ponytail: `structured` NO se persiste (solo respuesta viva; regenerable de tool_calls guardados).
- Verificado: tsc exit 0; self-check `_harvest_structured` (dedupe+guards+roundtrip ChatResponse) OK.
- Recarga: `structured` reaparece al recargar conversación SIN columna nueva — `routes._message_out` regenera determinista con `_harvest_structured(tool_calls)` (ahora acepta ToolCallOut o dicts persistidos). `MessageOut.structured`, `AiMessage.structured`, mapeo en `loadConversation`. Verificado tsc 0 + self-check harvest-from-dicts.

**HECHO (2026-07-12, sin commit) — AI-1 cancelación (sin SSE):**
- Botón Detener (Square) en `AiMessageInput` mientras `sending`; `useAiConversation.cancel()` aborta el AbortController en vuelo (guardado en `controllerRef`); flag `userCancelledRef` distingue cancelación de usuario (sin error) de timeout 130s (aviso). Wired en AssistantPage (`sending`+`onCancel`). tsc 0.
- ponytail: NO se hace SSE/streaming token-a-token — riesgo alto sobre el path de tools que funciona (la 1ª llamada no sabe a priori si es tool_call o texto; con modelos locales parsear tool_call en streaming es frágil). `stream_chat` YA existe en providers pero queda sin usar. El dolor real (espera muerta) lo resuelve cancelar.

**HECHO (2026-07-12, sin commit) — AI-2 tool trace legible:**
- `AiToolTrace` ya era chip colapsable; ahora el resumen colapsado dice "Datos usados: patrimonio, resumen mensual, cartera" (mapa `DATA_LABELS` nombre_tool→etiqueta humana, dedup por Set; fallback al nombre crudo si no está mapeada). Icono Wrench→Database. Detalle expandido muestra etiqueta humana + nombre técnico mono + ms/errores. tsc 0. Cliente-only, sin tocar backend.
- Página Asistente→Centro de Análisis con chat como pestaña secundaria: YA hecho en AI-3.

**HECHO (2026-07-12, sin commit) — AI-4 guardrails accionables (backend):**
- Whitelist de rutas: nuevo `backend/app/modules/ai/action_whitelist.py` (`is_allowed_action(target)`, frozenset `_ALLOWED_ROUTES` sacado de App.tsx + prefijo dinámico `/markets/`; ignora query/`#`, tolera trailing slash). Cableado en los DOS puntos que recogen `InsightActionOut`: `service._harvest_structured.add_action` (chat) y `analysis.build_bundle` (briefs) → un `target` con typo (`/investment`) se descarta en vez de pintar un botón que navega a pantalla inexistente. Las acciones ya eran deterministas (de reglas de insights, no del LLM); esto es defensa en profundidad.
- Guardrail de asesoramiento: `guardrails.enforce_advice_guardrail(text)` — NO reescribe el cuerpo (evita corromper "garantizado por el FGD"); regex `_ADVICE` de alta precisión (2ª persona "deberías/te recomiendo + comprar/vender/invertir/aportar/retirar/traspasar"; "rentabilidad/retorno/ganancia/beneficio + garantizad*") → si matchea, añade UNA nota neutral `_DISCLAIMER` al final. Idempotente. Cableado tras `sanitize_response` en service.py:246 (chat) y analysis.py (narrativa de brief).
- Verificado: self-checks `python -m action_whitelist` y `-m guardrails` OK (incluye no-falsos-positivos poder-de-compra/FGD e idempotencia); import backend OK. Sin cambio de frontend (las actions ya se pintan con navigate(target)). AI-4 parte 1 (actions→pantallas) ya estaba.

**HECHO (2026-07-12, sin commit) — AI-5 copiloto contextual (fuente de sugerencias unificada):**
- Backend ya cumplía la otra mitad: `service._with_screen_context` inyecta el contexto de pantalla filtrado por whitelist de claves (`module,route,period,visible_metrics,data_status,selected_entity,suggested_action,insight_id`) en el mensaje de usuario — no tocado.
- Hueco real cerrado: el empty-state del asistente tenía 3 preguntas fijas propias e ignoraba el contexto. Ahora `AiMessageList` acepta `suggestions?: string[]` (fallback = las 3 genéricas, `FALLBACK_SUGGESTIONS`); `AssistantPage` pasa `context.suggestedQuestions` (que llega vía `navigate('/assistant',{state:{prompt,context}})` desde el copiloto de RootLayout, cuyo contexto sale de `contextualCopilot.getCopilotContext(route)`). Resultado: si entras desde el copiloto de un módulo, el empty-state muestra las sugerencias de ESE módulo; si abres /assistant directo, las genéricas.
- Verificado: tsc --noEmit exit 0. Cliente-only.
- DEFERIDO (subjetivo / solapa dual-panel de AI-2): fundir el popover del copiloto (RootLayout) y la página del asistente en UN mismo componente. Sin el panel lateral dual (AI-2 deferido) no hay "segundo panel" que unificar; se hizo la unificación de comportamiento (misma fuente de contexto→sugerencias en las dos entradas), no la fusión de componentes.

**HECHO (2026-07-12, sin commit) — AI-3 D1 auto-generación del brief al arrancar:**
- Nuevo `backend/app/modules/ai/startup.py` (`launch_startup_brief()`): hilo daemon (patrón `launch_startup_ingest`), `asyncio.run(_run())`. Asegura `monthly_review` del mes en curso Y del mes anterior. Guardas: idempotente (`get_brief` existe→skip, no pisa narrativa LLM previa), datos no vacíos (`build_bundle[...]['data_state']!='empty'`), y provider LLM vivo (`get_provider().health().available`) — si el LLM está apagado NO persiste fallback determinista (que se quedaría congelado); lo genera el botón manual o el próximo arranque con LLM. best-effort: nunca tumba el arranque.
- "Hook cierre de mes" implícito: la 1ª apertura del mes nuevo genera el brief del mes anterior (que aún no existía). Sin scheduler (app de escritorio se abre a menudo).
- Cableado en `main.py` lifespan tras `launch_startup_ingest()`. Verificado: `python -m app.modules.ai.startup` (self-check períodos: 2026-07→06, 2026-01→2025-12) OK; `import app.main` OK. Frontend sin cambios (AnalysisCenter ya lista briefs al montar).

**PENDIENTE (deferido, gran esfuerzo):**
- AI-1: Streaming/SSE token-a-token (deferido a propósito, ver ponytail arriba; providers.stream_chat listo si se retoma). Cancelación YA hecha.
- AI-2 restante: shell Mercury/PageHeader (cosmético, subjetivo); sugerencias de arranque por estado real de datos (necesita fuente data_state en el empty state); panel lateral dual (solapa con AI-5).
- AI-3 scopes extra deferidos: weekly_brief/portfolio_health/budget_pulse (D2 = mensual primero). Nav sigue "Asistente" (D4 abierto). Auto-generación al arrancar + cierre de mes (D1): YA hecho.
- AI-4: acciones con whitelist de rutas (base puesta: bundle.actions ya salen de InsightActionOut). AI-5: unificar copiloto lateral contextual.

Restricción arquitectónica innegociable: LLM nunca calcula cifras ni decide qué analizar (redactor de bundle cerrado). Ver [[project_constraints]].


---
**Relacionadas:** [[project_constraints]] · [[project_redesign_proposal]]

Tags: #módulo #plan
