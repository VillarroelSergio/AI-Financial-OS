# Apple Restyling — Design Spec
**Date:** 2026-06-30
**Status:** Approved

## Overview

Restyling completo del Financial OS aplicando el design system Apple (obsidian gallery vitrine) definido en `docs/Styles/DESIGN.md` y `docs/Styles/variables.css`. El objetivo es una estética premium dark-first con tema claro/oscuro seleccionable desde configuración.

**Enfoque:** Opción B — restyling estructural. Tokens + tipografía + ajustes de layout en el shell de la app. Sin reescritura de lógica de negocio ni cambios en la estructura de páginas internas.

---

## Sección 1 — Sistema de tokens

### Método de theming

- Atributo `data-theme="dark" | "light"` en `<html>`
- Dos bloques de variables en `index.css`: `:root` (tokens base compartidos) + `[data-theme="dark"]` y `[data-theme="light"]`
- Persiste en `localStorage` clave `'theme'`, default `'dark'`
- Aplicado antes del primer render en `main.tsx` para evitar flash

### Variables semánticas — Dark theme

```css
[data-theme="dark"] {
  --bg-app: #000000;
  --bg-sidebar: #1d1d1f;
  --bg-surface: #111111;
  --bg-card: #1d1d1f;
  --bg-card-elevated: #333336;
  --bg-interactive: #333336;
  --text-primary: #f5f5f7;
  --text-secondary: #86868b;
  --text-muted: rgba(245, 245, 247, 0.5);
  --border-soft: #333336;
  --border-strong: #424245;
  --divider-soft: rgba(245, 245, 247, 0.1);
  --on-primary: #ffffff;
  --hairline-dark: #333336;
}
```

### Variables semánticas — Light theme

```css
[data-theme="light"] {
  --bg-app: #f5f5f7;
  --bg-sidebar: #1d1d1f;
  --bg-surface: #ffffff;
  --bg-card: #ffffff;
  --bg-card-elevated: #f5f5f7;
  --bg-interactive: #f5f5f7;
  --text-primary: #1d1d1f;
  --text-secondary: #86868b;
  --text-muted: rgba(29, 29, 31, 0.5);
  --border-soft: #e5e5e5;
  --border-strong: #cccccc;
  --divider-soft: rgba(29, 29, 31, 0.1);
  --on-primary: #ffffff;
  --hairline-dark: #cccccc;
}
```

### Tokens base compartidos (`:root`)

Todos los tokens de paleta nombrada de `variables.css` más los funcionales compartidos:

```css
:root {
  /* Paleta Apple */
  --color-obsidian: #1d1d1f;
  --color-frost-white: #f5f5f7;
  --color-pure-black: #000000;
  --color-paper-white: #ffffff;
  --color-carbon: #111111;
  --color-platinum: #86868b;
  --color-graphite: #333336;
  --color-silver-mist: #cccccc;
  --color-smoke: #424245;
  --color-apple-blue: #0071e3;
  --color-link-blue: #0066cc;
  --color-halo-blue: #2997ff;
  --color-signal-orange: #f56900;
  --color-iris-violet: #8668ff;
  --color-reef-teal: #00a1b3;

  /* Funcionales compartidos */
  --primary: #0071e3;
  --positive: #008163;
  --negative: #ee2526;
  --warning: #ff5c00;
  --info: #1b73e6;
  --accent: #f56900;

  /* Spacing (de variables.css) */
  --spacing-4: 4px;   --spacing-8: 8px;   --spacing-12: 12px;
  --spacing-16: 16px; --spacing-20: 20px; --spacing-24: 24px;
  --spacing-28: 28px; --spacing-32: 32px; --spacing-40: 40px;
  --spacing-48: 48px; --spacing-60: 60px; --spacing-76: 76px;
  --spacing-80: 80px; --spacing-96: 96px; --spacing-104: 104px;
  --spacing-160: 160px;

  /* Layout */
  --page-max-width: 1440px;
  --section-gap-min: 88px;
  --section-gap-max: 120px;
  --card-padding: 28px;
  --element-gap: 12px;

  /* Border Radius */
  --radius-links: 10px;
  --radius-cards: 28px;
  --radius-buttons: 36px;
  --radius-pill: 980px;
  --radius-nav: 980px;
}
```

### Tokens eliminados

Se eliminan todos los tokens del sistema anterior que no tienen equivalente:
`--color-bone-cream`, `--color-ember-orange`, `--color-pulse-violet`, `--color-cobalt-blue`, `--color-crimson`, `--color-caution-yellow`, `--color-voltage-green`, `--color-sky-cyan`, `--color-lime-pulse`, `--color-tangerine` (reemplazado por `--warning`), `--color-sage`, `--color-blush`, `--color-sand`, `--color-sky-tint`, `--color-celadon`, `--color-olive-slate`, `--color-forest-slate`, `--color-cocoa-slate`, `--color-plum-slate`, `--canvas-dark`, `--surface-deep`, `--stone`, `--mute`.

---

## Sección 2 — Tipografía

### Familias

```css
:root {
  --font-sf-pro-display: 'SF Pro Display', Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-sf-pro-text: 'SF Pro Text', Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
```

La familia del body global pasa a `--font-sf-pro-text`. Los headlines de sección usan `--font-sf-pro-display`.

Las fuentes anteriores (`--font-stabilgrotesk`, `--font-optimistic-text`, `--font-klarheitkurrent`) se eliminan. `--font-courier-new` se mantiene para `.financial-number`.

### Escala exacta (DESIGN.md)

```css
:root {
  --text-caption: 10px;    --leading-caption: 1.83;  --tracking-caption: -0.37px;
  --text-body: 14px;       --leading-body: 1.43;     --tracking-body: -0.22px;
  --text-heading-sm: 19px; --leading-heading-sm: 1.21; --tracking-heading-sm: -0.28px;
  --text-heading: 24px;    --leading-heading: 1.17;  --tracking-heading: -0.24px;
  --text-heading-lg: 32px; --leading-heading-lg: 1.14; --tracking-heading-lg: -0.32px;
  --text-display: 56px;    --leading-display: 1.07;  --tracking-display: -0.84px;
  --text-hero: 80px;       --leading-hero: 1.05;     --tracking-hero: -0.24px;

  --font-weight-regular: 400;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;
}
```

### Clases de utilidad añadidas

```css
.text-caption  { font-size: var(--text-caption);    line-height: var(--leading-caption);    letter-spacing: var(--tracking-caption); }
.text-body     { font-size: var(--text-body);       line-height: var(--leading-body);       letter-spacing: var(--tracking-body); }
.text-heading-sm { font-size: var(--text-heading-sm); line-height: var(--leading-heading-sm); letter-spacing: var(--tracking-heading-sm); }
/* etc. */
```

### `.financial-number`

```css
.financial-number {
  font-family: var(--font-courier-new);
  font-variant-numeric: tabular-nums lining-nums;
  font-feature-settings: "numr";
  letter-spacing: -0.07em;
}
```

`font-feature-settings: "ss02"` del `html` se elimina (era específico de StabilGrotesk).

---

## Sección 3 — Layout estructural

### Sidebar (`RootLayout.tsx`)

- Fondo: `--bg-sidebar` (`#1d1d1f`) en ambos temas
- Logo "Financial OS": `--font-sf-pro-display`, 19px / 600, `--text-primary` (Frost White siempre en sidebar)
- Subtítulo "Local finance system": 12px / 400, Platinum `#86868b`
- **Nav items:** se eliminan los fondos de color por ítem (`color` prop de navItems eliminada)
  - Inactivo: texto Platinum `#86868b`, sin fondo
  - Activo: fondo `#333336` Graphite, texto Frost White `#f5f5f7`, `border-radius: 10px`
  - Sin número de índice (01, 02...) — se elimina
  - Hover: `background: rgba(245,245,247,0.06)`
- Ancho sidebar: mantiene `192px`

### Nav mobile (`RootLayout.tsx`)

El bloque mobile (visible en `< lg`) tiene los mismos fondos de color por ítem. Se aplican los mismos cambios:
- Fondo barra mobile: `--bg-sidebar` (`#1d1d1f`)
- Nav items: scroll horizontal de pills con fondo `--bg-card-elevated` inactivo / `#333336` activo, texto Frost White, `border-radius: 10px`
- Se elimina la prop `color` y los `style` inline de color por ítem

### Header

- Fondo: `--bg-app`
- Texto: `--text-primary`
- Altura: 56px (de 72px)
- Tipografía: `--text-heading-sm` (19px / 400)

### Cards y superficies

- `border-radius: var(--radius-cards)` = 28px en todas las tarjetas
- Sin `box-shadow` (ya existía el override `!important`, se mantiene)
- Borde: 1px solid `var(--border-soft)`
- Padding: `var(--card-padding)` = 28px
- Clases `.premium-card` y `.mercury-panel` actualizadas

### Botones

- `.mercury-button-primary` → fondo `var(--primary)` (`#0071e3`), texto blanco, `border-radius: var(--radius-buttons)` (36px), `padding: 10px 20px`, 14px / 600
- `.mercury-button` → borde 1px `var(--border-soft)`, fondo transparente, `border-radius: var(--radius-buttons)`, hover con `opacity: 0.85`
- Se elimina el efecto `border-width` en hover

### Footer del layout

- La barra naranja `h-[6px] bg-ember-orange` → línea de 1px `border-top: 1px solid var(--border-soft)`

### Copilot panel

- Fondo card: `var(--bg-card)` con `border-radius: 28px`
- Sin `box-shadow`
- Borde: 1px `var(--border-soft)`

### Clases globales actualizadas

| Clase actual | Cambio |
|---|---|
| `.dashboard-grid` | Sin cambios funcionales, gap a `var(--spacing-16)` |
| `.premium-card` | `border-radius: 28px`, border 1px `var(--border-soft)`, bg `var(--bg-card)` |
| `.mercury-panel` | Igual que premium-card |
| `.mercury-button` | `border-radius: 36px`, border 1px, hover `opacity: 0.85` |
| `.mercury-button-primary` | Apple Blue fill, 36px radius |
| `::selection` | Background `var(--color-apple-blue)` con `opacity: 0.3`, texto `--text-primary` |
| Scrollbar track | `var(--bg-surface)` |
| Scrollbar thumb | `var(--border-strong)` |

---

## Sección 4 — Theme toggle en Settings

### Hook `src/lib/useTheme.ts`

```typescript
type Theme = 'dark' | 'light';

function getSystemTheme(): Theme {
  return 'dark'; // default
}

export function useTheme() {
  const stored = localStorage.getItem('theme') as Theme | null;
  const current = (document.documentElement.getAttribute('data-theme') as Theme) || stored || getSystemTheme();

  function setTheme(theme: Theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }

  return { theme: current, setTheme };
}
```

### Inicialización en `main.tsx`

Antes del `ReactDOM.createRoot(...)`:

```typescript
const stored = localStorage.getItem('theme') || 'dark';
document.documentElement.setAttribute('data-theme', stored);
```

### UI en `SettingsPage.tsx`

Nueva sección "Apariencia" con dos cards seleccionables:

- Card **Oscuro**: preview con fondo `#000000`, texto `#f5f5f7`
- Card **Claro**: preview con fondo `#f5f5f7`, texto `#1d1d1f`
- Card activa: borde 2px `#0071e3` Apple Blue
- Card inactiva: borde 1px `var(--border-soft)`
- `border-radius: 28px`, padding 16px
- Label debajo: "Oscuro" / "Claro" en `text-body`

---

## Archivos afectados

| Archivo | Tipo de cambio |
|---|---|
| `src/index.css` | Reescritura completa de variables + bloques de tema |
| `src/main.tsx` | Añadir inicialización de tema antes del render |
| `src/lib/useTheme.ts` | Nuevo hook |
| `src/app/layout/RootLayout.tsx` | Sidebar, nav items, header, footer |
| `src/features/settings/SettingsPage.tsx` | Nueva sección Apariencia |

Los componentes internos de páginas (MetricCard, Dashboard, etc.) **no requieren cambios de código** si usan clases semánticas (`bg-card`, `text-primary`, etc.) o las clases globales `.premium-card` / `.mercury-button`. Si algún componente usa tokens hardcoded del sistema anterior, se actualiza puntualmente durante implementación.

---

## Restricciones (Do's and Don'ts del DESIGN.md)

- **No** `box-shadow` en ningún elemento UI — profundidad solo por contraste de superficie
- **No** más de un botón Apple Blue por viewport — es el único CTA cromático
- **No** colores de acento (signal orange, iris violet, reef teal) en texto de párrafo o fondos grandes
- **No** `border-radius` fuera del set definido: 10px / 28px / 36px / 980px
- **No** gradientes ni texturas decorativas
- Signal Orange `#f56900` únicamente para badges de categoría (eyebrows)
- Texto de párrafo en dark: Frost White `#f5f5f7`, nunca `#ffffff` puro
- Texto de párrafo en light: Obsidian `#1d1d1f` o Platinum `#86868b`
