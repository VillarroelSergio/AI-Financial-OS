---
name: feedback_startup_animation
description: La animación de inicio debe ejecutarse en cada arranque y no puede perderse al refactorizar App o la estrategia de carga.
metadata:
  type: feedback
---

# Animación de inicio obligatoria

- Debe mostrarse en **cada arranque** de la aplicación, con la duración acordada de 2,4 s.
- No debe degradarse a un spinner ni desaparecer al modificar `App.tsx` o `main.tsx`.
- La carga mantiene todas las pantallas disponibles desde el inicio; no se reintroduce carga diferida por módulo.

Relacionadas: [[project_constraints]] · [[feedback_ux_snapshots]]

Tags: #feedback #animación #arranque #decisión
