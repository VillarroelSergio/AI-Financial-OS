# 09 — Design System

> **Fuente base:** `DESIGN-revolut.md` — todos los tokens de color, tipografía, spacing y border-radius se derivan de ese archivo. Las adaptaciones para desktop se documentan explícitamente en cada sección.

---

## Principio rector

La interfaz trabaja en un único canvas oscuro (no hay modo claro en V1). La profundidad se logra exclusivamente mediante diferencias de luminancia entre superficies, nunca con sombras. El color de marca (cobalt violet `#494fdf`) aparece con parsimonia: botones primarios destacados, badges de énfasis y el logotipo.

---

## Colores

### Tokens del sistema (heredados de Revolut)

Todos los valores son exactos del archivo fuente. Solo se usa el subconjunto dark.

```
canvas-dark:      #000000   ← fondo base de toda la app
surface-deep:     #0a0a0a   ← sidebar, paneles laterales
surface-elevated: #16181a   ← cards, paneles secundarios
hairline-dark:    rgba(255,255,255,0.12)  ← bordes de cards
divider-soft:     rgba(255,255,255,0.06)  ← separadores internos
on-dark:          #ffffff   ← texto primario
on-dark-mute:     rgba(255,255,255,0.72) ← texto secundario
stone:            #8d969e   ← texto terciario / labels inactivos
mute:             #505a63   ← texto deshabilitado
faint:            #c9c9cd   ← estados deshabilitados sobre dark

primary:          #494fdf   ← cobalt violet — solo donde tiene peso
primary-bright:   #4f55f1   ← hover/focus de primary
primary-deep:     #3a40c4   ← pressed de primary
on-primary:       #ffffff   ← texto sobre primary
```

### Palette semántica (Revolut accents → roles financieros)

```
accent-teal:      #00a87e   → success: ahorro positivo, progreso, ganancias
accent-danger:    #e23b4a   → danger: gasto elevado, pérdida, error destructivo
accent-warning:   #ec7e00   → warning: dato incompleto, atención
accent-yellow:    #b09000   → caution: pendiente, sin confirmar
accent-blue-link: #376cd5   → info: datos de mercado, economía, links
accent-pink:      #e61e49   → uso reservado para iconografía de categorías
```

### Usos prohibidos (heredados de Revolut)

- No usar `accent-*` como fondo de botones. Viven en iconografía y badges informativos.
- No usar `#0a0a0a` como fondo base. El canvas base es `#000000`.
- No añadir sombras (`box-shadow`). La profundidad es solo luminancia.
- No mezclar más de dos pasos del surface ladder por pantalla (`canvas-dark` → `surface-elevated`).
- No usar `primary` como color de texto en prose. Solo en superficies de énfasis.

---

## Tipografía

### Familia tipográfica

Revolut usa **Aeonik Pro** (propietaria) para display y **Inter** para body. En esta app se usa **Inter** para todo — es la alternativa libre recomendada por el propio sistema Revolut.

Ajuste obligatorio al usar Inter en lugar de Aeonik Pro: aplicar `letter-spacing: -0.01em` en tokens de display para replicar el apretado característico.

```
font-family: "Inter", ui-sans-serif, sans-serif
```

### Escala de tokens (adaptada para desktop)

Los tamaños de display xxl / xl del sistema Revolut (136px, 80px) no aplican en un dashboard de escritorio. Se conservan los tamaños a partir de `display-lg` hacia abajo.

| Token | Size | Weight | Line Height | Letter Spacing | Uso en la app |
|---|---|---|---|---|---|
| `display-lg` | 48px | 600 | 1.21 | -0.48px | Título principal de página (uso puntual) |
| `heading-lg` | 32px | 600 | 1.19 | -0.32px | Títulos de sección / pantalla |
| `heading-md` | 24px | 600 | 1.33 | 0 | Subtítulos de sección |
| `heading-sm` | 20px | 500 | 1.4 | 0 | Títulos de card, metric labels grandes |
| `body-lg` | 18px | 400 | 1.56 | -0.09px | Valores de métrica principal |
| `body-md` | 16px | 400 | 1.5 | 0.24px | Texto base, descripciones |
| `body-md-bold` | 16px | 600 | 1.5 | 0.16px | Énfasis de texto base |
| `body-sm` | 14px | 400 | 1.43 | 0 | Metadata, labels de nav, captions |
| `button-md` | 16px | 600 | 1.5 | 0.24px | Labels de botón principal |
| `button-sm` | 14px | 600 | 1.43 | 0 | Labels de botón secundario, pills |
| `caption` | 13px | 400 | 1.4 | 0 | Fechas, fuentes de datos, notas |

### Principios

- Pesos permitidos: 400 (regular), 500 (medium), 600 (semibold). No usar 700 en UI general.
- Valores monetarios y métricas: `body-lg` o `heading-sm` según la prominencia.
- Labels de navegación y metadata: `body-sm`.
- No usar el mismo peso para texto principal e información de apoyo en la misma card.

---

## Spacing

Base 4px. Tokens exactos de Revolut:

```
xxs:  4px
xs:   6px
sm:   8px
md:   14px
lg:   16px
xl:   24px
xxl:  32px
xxxl: 48px
```

### Usos en desktop

```
padding interno de card:   xl (24px) o xxl (32px)
gap entre cards en grid:   xl (24px)
padding de página:         xxl (32px) horizontal, xl (24px) vertical
altura de sidebar:         100vh, ancho fijo 240px
padding de nav item:       sm (8px) vertical, md (14px) horizontal
gap entre items de nav:    xs (6px)
```

---

## Border Radius

Tokens exactos de Revolut:

```
rounded-none: 0px
rounded-sm:   8px    ← chips, badges, tags
rounded-md:   12px   ← inputs, selects, tiles pequeños
rounded-lg:   20px   ← cards principales, paneles
rounded-xl:   28px   ← modales, drawers, paneles flotantes
rounded-full: 9999px ← botones, pills, avatares
```

---

## Elevación y profundidad

Sin sombras. La jerarquía visual es solo luminancia:

| Nivel | Surface | Token | Uso |
|---|---|---|---|
| 0 | Base | `canvas-dark` `#000000` | Fondo de toda la app |
| 1 | Sidebar / paneles laterales | `surface-deep` `#0a0a0a` | Sidebar, panel IA |
| 2 | Cards / paneles secundarios | `surface-elevated` `#16181a` | MetricCard, ChartCard, tablas |
| 3 | Énfasis de marca | `primary` `#494fdf` | Botón primario destacado, badge featured |

Bordes: `hairline-dark` (`rgba(255,255,255,0.12)`) en todos los elementos de nivel 2. Separadores internos: `divider-soft` (`rgba(255,255,255,0.06)`).

---

## Componentes

### Botones

**`button-primary`** — acción principal destacada
- Background `primary` (`#494fdf`), texto `on-primary` (`#fff`), `button-md`, `rounded-full`, height 40px, padding 10px 24px.
- Hover: `primary-bright`. Pressed: `primary-deep`.
- Usar solo para la acción más importante de la pantalla (ej. "Confirmar importación").

**`button-secondary`** — acción secundaria sobre dark
- Background `surface-elevated` (`#16181a`), texto `on-dark`, borde `hairline-dark`, `button-sm`, `rounded-full`, height 36px, padding 8px 16px.
- Hover: `hairline-dark` → `rgba(255,255,255,0.20)`.

**`button-ghost`** — acción terciaria / destructiva leve
- Background transparente, texto `stone`, `button-sm`, `rounded-md`, height 36px.
- Hover: texto `on-dark`.

**`button-danger`** — acción destructiva
- Background `accent-danger` (`#e23b4a`), texto `#fff`, `button-md`, `rounded-full`, height 40px.
- Usar solo para acciones irreversibles con confirmación previa.

**`button-pill-sm`** — filtros, tabs, chips
- Background `surface-elevated`, texto `stone`, `button-sm`, `rounded-full`, padding 6px 14px, height 32px.
- Activo: background `primary`, texto `on-primary`.

### Cards

**`card`** — card estándar
- Background `surface-elevated` (`#16181a`), borde 1px `hairline-dark`, `rounded-lg`, padding `xl` (24px).

**`card-featured`** — card con énfasis de marca
- Background `primary` (`#494fdf`), sin borde, `rounded-lg`, padding `xl`.
- Usar con parsimonia — máximo uno por viewport.

### MetricCard

Card de métrica financiera. Uso en dashboard Overview y Spending.

```
Propiedades:
  title          — label de la métrica (body-sm, stone)
  value          — valor principal (heading-sm o body-lg, on-dark)
  unit           — moneda o % (caption, stone)
  variation      — cambio vs periodo anterior (body-sm, accent-teal / accent-danger)
  variationLabel — "vs mes anterior" (caption, mute)
  period         — periodo de referencia (caption, stone)
  status         — success | warning | danger | neutral (color del borde superior)
```

Borde superior de 2px con el color semántico del estado. Sin borde lateral ni sombra.

### ChartCard

```
Propiedades:
  title      — heading-sm, on-dark
  subtitle   — body-sm, stone
  chart      — área del gráfico (Recharts)
  legend     — leyenda opcional
  actions    — slot de acciones (periodo, filtro)
  emptyState — slot cuando no hay datos
```

Padding interno `xxl` (32px). El chart ocupa el ancho completo hasta los bordes del padding.

### InsightCard

```
Propiedades:
  title      — body-md-bold, on-dark
  message    — body-sm, on-dark-mute
  severity   — info | success | warning | danger
  dataSource — caption, stone
  cta        — acción opcional
```

Borde izquierdo de 3px con el color semántico de `severity`:
- info → `accent-blue-link`
- success → `accent-teal`
- warning → `accent-warning`
- danger → `accent-danger`

### Inputs y formularios

**`text-input`**
- Background `surface-elevated`, texto `on-dark`, placeholder `stone`.
- Borde: 1px `hairline-dark`. Focus: 1px `primary-bright`.
- `body-md`, `rounded-md`, height 44px, padding 10px 14px.

**`select`**
- Mismo estilo que `text-input`. Icono ChevronDown en `stone`.

**`text-area`**
- Mismo estilo que `text-input`. Altura mínima 96px.

### Navegación lateral (Sidebar)

- Background `surface-deep` (`#0a0a0a`), ancho 240px fijo.
- Separador derecho: 1px `hairline-dark`.
- Logo / app name: `heading-sm`, `on-dark`, padding `xxl` (32px) lateral, altura 56px.
- Nav items: `body-sm`, padding 8px 14px, `rounded-md`, gap 4px entre items.
  - Inactivo: texto `stone`. Hover: texto `on-dark`, background `surface-elevated/50`.
  - Activo: texto `on-dark`, background `surface-elevated`.
- Icono: 16px, alineado con el texto a 12px de distancia.

### Badges y tags

**`badge-semantic`** — estado de dato financiero
- Pill con fondo semitransparente del color semántico + texto del mismo color.
  - success: background `accent-teal/15`, texto `accent-teal`
  - danger: background `accent-danger/15`, texto `accent-danger`
  - warning: background `accent-warning/15`, texto `accent-warning`
  - info: background `accent-blue-link/15`, texto `accent-blue-link`
- `caption`, `rounded-full`, padding 3px 10px.

**`badge-tag`** — etiqueta neutra (categorías, filtros)
- Background `surface-elevated`, texto `stone`, borde `hairline-dark`.
- `caption`, `rounded-sm`, padding 3px 8px.

**`badge-featured`** — énfasis de marca
- Background `primary`, texto `on-primary`.
- `caption`, `rounded-full`, padding 3px 10px.

### Tabla de datos

- Header: `caption`, `stone`, uppercase, borde inferior `hairline-dark`.
- Filas: `body-sm`, `on-dark`. Hover: background `surface-elevated/50`.
- Separador entre filas: `divider-soft`.
- Padding de celda: sm (8px) vertical, xl (24px) horizontal en primera y última columna.

### EmptyState

```
Propiedades:
  icon    — Lucide icon, 32px, stone
  title   — heading-sm, on-dark
  message — body-sm, stone
  cta     — button-secondary opcional
```

Centrado vertical y horizontalmente en el área de contenido. Sin ilustraciones decorativas en V1.

### Skeleton loading

- Rectángulo con background `surface-elevated`, borde-radius según el elemento que sustituye.
- Animación: `opacity` 0.4 → 0.8 a 1.2s loop. Sin gradiente animado en V1.

### Panel IA (AI_SIDE_PANEL)

- Posición: lateral derecho, anchura 360px, altura 100%.
- Background `surface-deep`, borde izquierdo `hairline-dark`.
- Entrada de texto: `text-input` al pie del panel.
- Mensajes del asistente: card con `rounded-lg`, background `surface-elevated`.
- Datos citados: badge semántico `info` con el nombre del tool usado.
- Transición de apertura: `transform translateX` 360px → 0, 200ms ease-out.

### ImportStepper

```
Propiedades:
  steps       — array de labels
  currentStep — índice activo
  status      — idle | loading | error | success
```

- Indicadores de paso: círculo 24px. Completado: `accent-teal`. Activo: `primary`. Pendiente: `surface-elevated` con borde `hairline-dark`.
- Línea conectora: 1px `hairline-dark`. Completada: `accent-teal`.

---

## Gráficas (Recharts)

Colores para series de datos (en este orden):

```
1. #494fdf  (primary)
2. #00a87e  (accent-teal)
3. #376cd5  (accent-blue-link)
4. #e23b4a  (accent-danger)
5. #ec7e00  (accent-warning)
6. #b09000  (accent-yellow)
```

Reglas:
- Grid lines: `divider-soft` (`rgba(255,255,255,0.06)`).
- Axis labels: `caption`, `stone`.
- Tooltip: background `surface-elevated`, borde `hairline-dark`, `rounded-md`.
- No usar 3D. No usar pie charts excepto para distribución simple (máx. 6 segmentos).
- No usar velas japonesas en V1.
- AreaChart con `fillOpacity: 0.1` del color de la serie.

---

## Iconografía

Librería: **Lucide Icons** — consistente, outline, tamaños estándar.

```
Tamaños permitidos: 14px, 16px, 20px, 24px, 32px
Color por defecto: stone (#8d969e)
Color activo / énfasis: on-dark (#ffffff)
Color semántico: el accent correspondiente al estado
```

No combinar iconos de distintas familias.

---

## Motion

```
Duración estándar:     150ms
Duración de paneles:   200ms
Duración de modales:   250ms
Easing:                ease-out (entrada), ease-in (salida)
```

Transiciones aplicadas:
- Nav items: `color`, `background-color` — 150ms.
- Hover de cards: `border-color` — 150ms.
- Panel IA: `transform`, `opacity` — 200ms.
- Skeleton: `opacity` — 1200ms loop.
- Stepper: `background-color`, `border-color` — 200ms.

No usar animaciones decorativas, parallax ni motion que consuma atención visual sin aportar información.

---

## Accesibilidad

- Contraste mínimo AA (4.5:1) para texto sobre superficies. `on-dark` sobre `surface-elevated` cumple.
- Focus visible: outline 2px `primary-bright`, offset 2px. No usar `outline: none` sin alternativa.
- Navegación por teclado: todos los elementos interactivos accesibles con Tab y Enter/Space.
- No comunicar estado financiero solo por color — incluir icono o label siempre.
- Labels en todos los inputs. No usar placeholder como label.
- Altura mínima de targets interactivos: 36px.

---

## Estados de componente

Todo componente que muestre datos debe implementar los cinco estados:

```
loading  — Skeleton del mismo tamaño y forma que el contenido real
empty    — EmptyState con mensaje descriptivo en español
error    — InsightCard severity: danger con mensaje de error y acción de reintento
partial  — Dato disponible parcialmente, badge warning con contexto
success  — Estado normal con datos completos
```

---

## Regla de densidad

Una pantalla no debe superar 6–8 métricas visibles simultáneamente sin un mecanismo de profundización (tabs, drill-down, modal). Si una card requiere más de 4 líneas de texto para ser comprensible, está haciendo demasiado.

---

## Do's y Don'ts del sistema

### Do
- Usar `surface-elevated` como fondo de todas las cards. Nunca `canvas-dark` directamente en una card.
- Usar `button-primary` (primary violet) solo para la acción más importante de la pantalla.
- Reservar los accents semánticos para comunicar estado financiero — no como decoración.
- Usar `rounded-full` en botones y pills; `rounded-lg` en cards; `rounded-md` en inputs.
- Usar `hairline-dark` como único borde visible. Sin bordes decorativos adicionales.
- Mantener el sidebar siempre en `surface-deep` — nunca `surface-elevated`.

### Don't
- No agregar `box-shadow`. La profundidad es solo luminancia entre superficies.
- No usar `primary` como color de texto en prose o labels generales.
- No mostrar más de un `card-featured` (primary background) por viewport.
- No usar `accent-pink` ni `accent-brown` fuera de iconografía de categorías.
- No mezclar Recharts con otra librería de gráficas.
- No usar animaciones de más de 300ms en respuesta a interacciones del usuario.
