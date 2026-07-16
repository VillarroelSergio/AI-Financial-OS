---
name: project-redesign-proposal
description: "Rediseño UX/UI — usuario ELIGIÓ C·Atelier (2026-07-12); spec completa en docs/20_REDESIGN_ATELIER.md, pendiente de implementar (Opus 4.8)"
metadata: 
  node_type: memory
  type: project
  originSessionId: ac090904-498b-454d-ab9f-60c9f2c64687
---

El 2026-07-12 se presentó una propuesta de rediseño UX/UI para convertir la app en producto profesional.
Artifact: https://claude.ai/code/artifact/a5f759ec-d1d9-484a-8a05-4f13feeafc79

Diagnóstico principal: H1 de 80px devora pantalla, Courier New en cifras, sin jerarquía de superficie (`box-shadow: none !important` en index.css), cromo duplicado, dashboard sin deltas/tendencia/insights, motion casi ausente, empty states pobres, idioma inconsistente.

Tres direcciones: A·Ledger (fintech oscuro tipo Linear/Mercury, ⌘K, mono moderna en cifras — RECOMENDADA), B·Terminal (Bloomberg-like, cinta + línea de comandos), C·Atelier (Apple light-first, hero de patrimonio, springs).

DECISIÓN (2026-07-12): el usuario eligió **C·Atelier** (light-first). Esto SUPERSEDE la restricción "Mantener estilo Dark Premium" de [[project-constraints]]; el tema oscuro se mantiene soportado pero el default pasa a claro. Spec de implementación completa (6 fases, tokens exactos, motion spec, criterios de aceptación) en `AI-Financial-OS/docs/20_REDESIGN_ATELIER.md`, escrita para que la implemente Opus 4.8. Única dependencia nueva permitida: framer-motion. Implementación aún NO iniciada.


---
**Relacionadas:** [[project_ai_module_plan]] · [[project_v1_release_prep]]

Tags: #diseño #decisión
