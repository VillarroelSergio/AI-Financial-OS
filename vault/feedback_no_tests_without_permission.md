---
name: feedback_no_tests_without_permission
description: "No ejecutar tests (pytest, suites, etc.) sin permiso explícito del usuario"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: cca0ad7e-cebb-4e6f-ab7f-759ef609384f
---

No ejecutar tests sin permiso explícito del usuario (2026-07-03, sesión FinancialAgent).

**Why:** El usuario interrumpió dos veces una ejecución de pytest lanzada por iniciativa propia y pidió grabarlo en memoria.

**How to apply:** Antes de lanzar cualquier suite de tests (pytest, vitest, cargo test, ux:snapshots incluidos solo si él lo pide — ver [[feedback_ux_snapshots]]), preguntar primero o esperar a que el usuario lo pida. Los smoke-checks triviales de import/config también conviene consultarlos si se parecen a tests. Relacionado: [[feedback_commits_and_graphify]].


---
**Relacionadas:** [[feedback_commits_and_graphify]] · [[feedback_ux_snapshots]]

Tags: #feedback #proceso
