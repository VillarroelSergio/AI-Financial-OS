# AGENTS.md — Base de conocimiento y memoria (Claude + Codex)

Todo el conocimiento del proyecto (documentación **y** memoria) vive en la bóveda de Obsidian
**`vault/`** (dentro de `AI-Financial-OS/`). Es la **única fuente de verdad**.

## Al empezar cada sesión
Entra por **`vault/Home.md`**: es el índice maestro (mapas por área / MOCs) y enlaza toda la
documentación y la memoria. Para estado y preferencias rápidas: **`vault/MEMORY.md`**.

La documentación de producto / arquitectura / dominio está en **`vault/docs/`** y se navega desde
los MOCs de `Home.md`. Consulta ahí antes de preguntar o asumir.

**Busca antes de asumir:** ante cualquier duda de arquitectura o dominio, busca en `vault/docs/`
entrando por el MOC correspondiente (desde `Home.md`) y en `vault/GLOSARIO.md` **antes** de leer
código o preguntar. Empieza cada sesión leyendo `vault/ESTADO.md` para saber dónde estamos.

## Al aprender algo que deba persistir entre sesiones
Guárdalo como nota Markdown en `vault/` (una nota = un hecho) con:
- Frontmatter: `name`, `description`, `metadata.type` = `user` | `feedback` | `project` | `reference`.
- Enlaces `[[nombre_de_fichero]]` (nombre exacto del `.md` sin extensión, **guion bajo** no guion).
- Tags al pie (`#feedback` `#módulo` `#decisión` …).

Después añade la línea al índice `vault/MEMORY.md` y enlázala desde el MOC que corresponda.
Las **decisiones de arquitectura** se guardan como ADR y se enlazan desde `MOC - Decisiones`.
**No dupliques**: si ya existe una nota del tema, actualízala.

Usa las plantillas de `vault/templates/` (`_template_nota_memoria.md`, `_template_ADR.md`) para
no inventar campos del frontmatter. Tras cerrar una tarea, actualiza `vault/ESTADO.md`.

## Reglas
- **No** escribas memoria del proyecto fuera de `vault/`.
- No hagas commits automáticos: deja los cambios en *stage* y pide confirmación
  (ver `vault/feedback_commits_and_graphify.md`).
- Responde al usuario en español.
