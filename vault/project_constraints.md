---
name: project_constraints
description: Restricciones obligatorias del proyecto AI Financial OS — qué no implementar y stack requerido
metadata: 
  node_type: memory
  type: project
  originSessionId: 85220b06-0251-459f-9270-e1392dcfec9e
---

# Restricciones obligatorias (Prompt Maestro)

- NO implementar automatización bancaria ni scraping
- NO leer email
- NO usar cloud para datos personales (local-first absoluto)
- NO implementar IA antes de que el core financiero esté completo (Fase 6+)
- NO permitir que el LLM consulte SQL directamente
- NO sobrecargar la UI
- Mantener estilo Dark Premium
- Mantener idioma español en toda la UI

# Stack obligatorio

Frontend: Tauri + React + TypeScript + Tailwind + **shadcn/ui** + **Recharts**
Backend: Python + FastAPI + SQLite + DuckDB
IA local: preparado para Ollama y LM Studio (sin implementar hasta Fase 6)

**Why:** Decisiones de diseño cerradas desde el inicio del proyecto para evitar derive de alcance.
**How to apply:** Antes de implementar cualquier feature, verificar que no viole ninguna de estas restricciones. shadcn/ui y Recharts son obligatorios — no sustituir por otras librerías de componentes o charts.


---
**Relacionadas:** [[project_investments_module]] · [[project_economy_plan]] · [[project_markets_module]] · [[project_ai_module_plan]] · [[project_v1_release_prep]]

Tags: #base #decisión
