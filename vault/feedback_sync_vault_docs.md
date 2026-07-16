---
name: feedback_sync_vault_docs
description: Siempre que un cambio requiera actualizar documentación, actualizar la bóveda del proyecto
metadata:
  type: feedback
---

Cada vez que hagamos cambios en el proyecto que requieran actualizar documentación,
hay que actualizar la bóveda de Obsidian (`vault/`): la nota de `docs/` correspondiente,
su MOC en `Home.md`, y `ESTADO.md`/`MEMORY.md` según toque. La bóveda es la única
fuente de verdad, así que la doc no vive en ningún otro sitio.

**Por qué:** la bóveda es la única fuente de verdad del proyecto (reglas de `AGENTS.md`).
Si la documentación no se sincroniza con los cambios, la bóveda queda desactualizada y deja
de ser fiable como referencia entre sesiones.

**Cómo aplicarlo:** al cerrar una tarea que toque comportamiento, arquitectura o dominio,
actualiza la nota de `docs/` afectada (una nota = un hecho, no dupliques), enlázala desde su MOC,
y refleja el estado en `ESTADO.md`. Las decisiones de arquitectura van como ADR
(ver [[MOC - Decisiones]]). No hagas commit automático: deja en stage y pide confirmación
(ver [[feedback_commit_confirmation]]).

---
**Relacionadas:** [[feedback_commit_confirmation]] [[feedback_ux_snapshots]]

Tags: #feedback #documentacion #proceso
