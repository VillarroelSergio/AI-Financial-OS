---
name: feedback-commits-and-graphify
description: Commits siempre manuales por el usuario; graphify al inicio y fin de cada instrucción
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 09db2d36-c8c0-4253-9096-378c274caf31
---

**Regla 1 — No commits automáticos:**
Nunca hacer `git commit` de forma automática. Solo preparar los cambios (stage). El usuario hace los commits manualmente. Si un subagente o el proceso requiere un commit, dejarlo pendiente y notificarlo.

**Why:** El usuario quiere control total sobre el historial de git.

**How to apply:** Al finalizar cada tarea, hacer `git add` de los ficheros pero no `git commit`. Indicar al usuario qué ficheros están staged y qué mensaje de commit se recomienda.

---

**Regla 2 — Graphify solo con permiso explícito (actualizado 2026-07-04):**
NO invocar `/graphify` automáticamente ni al inicio ni al final. Consultar al usuario antes de cualquier ejecución de graphify.

**Why:** Ahorrar tokens de ejecución. El usuario lo pidió explícitamente el 2026-07-04 (sustituye la regla anterior de graphify al inicio y fin).

**How to apply:** Si el grafo podría ayudar o convendría actualizarlo tras cambios, preguntar primero: "¿Quieres que ejecute graphify?". Igual que con los tests (ver [[feedback-no-tests-without-permission]]): nunca sin permiso previo.


---
**Relacionadas:** [[feedback_commit_confirmation]] · [[feedback_no_tests_without_permission]]

Tags: #feedback #proceso
