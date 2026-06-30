# Apple Restyling — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aplicar el design system Apple (dark/light themes) a Financial OS actualizando tokens CSS, Tailwind config, RootLayout y añadiendo toggle de tema en Settings.

**Architecture:** CSS custom properties en `index.css` con bloques `[data-theme="dark"]` / `[data-theme="light"]`. Tailwind config mapea sus nombres de color a esas variables via `var()`, haciendo que todos los componentes existentes adopten el nuevo tema sin cambios en los TSX de páginas internas. Solo se modifican `RootLayout.tsx` (sidebar, nav) y `SettingsPage.tsx` (toggle).

**Tech Stack:** Vite + React + TypeScript + Tailwind CSS v3 + CSS custom properties

## Global Constraints

- No `box-shadow` en ningún elemento UI — profundidad solo por contraste de superficie
- Solo un botón Apple Blue (`#0071e3`) por viewport como CTA primario
- `border-radius` permitidos: `10px` / `28px` / `36px` / `980px` únicamente
- Signal Orange `#f56900` solo en badges de categoría, nunca en texto párrafo ni fondos
- Texto párrafo en dark: `#f5f5f7` (nunca `#ffffff` puro); en light: `#1d1d1f` o `#86868b`
- Fuente body: SF Pro Text con fallback Inter. Fuente display: SF Pro Display con fallback Inter
- Sidebar siempre oscuro (`#1d1d1f`) en ambos temas
- Tema default: `dark`. Persiste en `localStorage` clave `'theme'`
- Sin dependencias npm nuevas
- Comando dev: `npm run dev` desde `apps/desktop/`

---

## File Map

| Archivo | Acción | Responsabilidad |
|---|---|---|
| `apps/desktop/src/index.css` | Reescritura | Tokens base, bloques dark/light, clases globales |
| `apps/desktop/tailwind.config.ts` | Modificar | Mapear colores a CSS vars, actualizar fuentes/radii/escala |
| `apps/desktop/src/main.tsx` | Modificar | Init de tema antes del primer render |
| `apps/desktop/src/lib/useTheme.ts` | Crear | Hook para leer/cambiar tema |
| `apps/desktop/src/app/layout/RootLayout.tsx` | Modificar | Sidebar, nav desktop+mobile, header, footer |
| `apps/desktop/src/features/settings/SettingsPage.tsx` | Modificar | Sección Apariencia con selector de tema |

---

## Task 1: CSS Variables + Theme Blocks

**Files:**
- Modify: `apps/desktop/src/index.css`

**Interfaces:**
- Produces: Variables CSS disponibles globalmente — `--bg-app`, `--bg-sidebar`, `--bg-card`, `--bg-card-elevated`, `--bg-surface`, `--bg-interactive`, `--text-primary`, `--text-secondary`, `--text-muted`, `--border-soft`, `--border-strong`, `--divider-soft`, `--primary`, `--positive`, `--negative`, `--warning`, `--info`, `--accent`, `--on-primary`, `--hairline-dark`, `--page-max-width`, `--card-padding`, `--element-gap`, `--radius-links`, `--radius-cards`, `--radius-buttons`, `--radius-pill`, `--font-sf-pro-display`, `--font-sf-pro-text`, `--font-courier-new`, y toda la escala tipográfica y de espaciado

- [ ] **Step 1: Reemplazar completamente el contenido de `index.css`**

El contenido completo del archivo debe ser:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* ─── Paleta Apple + Tokens base (compartidos entre temas) ─── */
:root {
  /* Paleta nombrada */
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
  --on-primary: #ffffff;

  /* Tipografía — Familias */
  --font-sf-pro-display: 'SF Pro Display', Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-sf-pro-text: 'SF Pro Text', Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-courier-new: "Courier New", ui-monospace, monospace;

  /* Tipografía — Escala exacta DESIGN.md */
  --text-caption: 10px;      --leading-caption: 1.83;     --tracking-caption: -0.37px;
  --text-body: 14px;         --leading-body: 1.43;        --tracking-body: -0.22px;
  --text-heading-sm: 19px;   --leading-heading-sm: 1.21;  --tracking-heading-sm: -0.28px;
  --text-heading: 24px;      --leading-heading: 1.17;     --tracking-heading: -0.24px;
  --text-heading-lg: 32px;   --leading-heading-lg: 1.14;  --tracking-heading-lg: -0.32px;
  --text-display: 56px;      --leading-display: 1.07;     --tracking-display: -0.84px;
  --text-hero: 80px;         --leading-hero: 1.05;        --tracking-hero: -0.24px;

  /* Tipografía — Pesos */
  --font-weight-regular: 400;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;

  /* Espaciado */
  --spacing-4: 4px;    --spacing-8: 8px;    --spacing-12: 12px;
  --spacing-16: 16px;  --spacing-20: 20px;  --spacing-24: 24px;
  --spacing-28: 28px;  --spacing-32: 32px;  --spacing-40: 40px;
  --spacing-48: 48px;  --spacing-60: 60px;  --spacing-76: 76px;
  --spacing-80: 80px;  --spacing-96: 96px;  --spacing-104: 104px;
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

/* ─── Tema Oscuro (default) ─── */
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
  --hairline-dark: #333336;
}

/* ─── Tema Claro ─── */
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
  --hairline-dark: #e5e5e5;
}

/* ─── Reset base ─── */
*,
*::before,
*::after {
  box-sizing: border-box;
}

html,
body,
#root {
  height: 100%;
  margin: 0;
  padding: 0;
  background: var(--bg-app);
  color: var(--text-primary);
  font-family: var(--font-sf-pro-text);
  font-feature-settings: "numr";
  -webkit-font-smoothing: antialiased;
  text-rendering: geometricPrecision;
}

body {
  overflow: hidden;
}

button,
a,
select,
input,
textarea {
  outline: none;
  font: inherit;
}

button:focus-visible,
a:focus-visible,
select:focus-visible,
input:focus-visible,
textarea:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}

/* ─── Clases de utilidad tipográfica ─── */
.text-caption    { font-size: var(--text-caption);    line-height: var(--leading-caption);    letter-spacing: var(--tracking-caption); }
.text-body       { font-size: var(--text-body);       line-height: var(--leading-body);       letter-spacing: var(--tracking-body); }
.text-heading-sm { font-size: var(--text-heading-sm); line-height: var(--leading-heading-sm); letter-spacing: var(--tracking-heading-sm); }
.text-heading    { font-size: var(--text-heading);    line-height: var(--leading-heading);    letter-spacing: var(--tracking-heading); }
.text-heading-lg { font-size: var(--text-heading-lg); line-height: var(--leading-heading-lg); letter-spacing: var(--tracking-heading-lg); }
.text-display    { font-size: var(--text-display);    line-height: var(--leading-display);    letter-spacing: var(--tracking-display); font-family: var(--font-sf-pro-display); }
.text-hero       { font-size: var(--text-hero);       line-height: var(--leading-hero);       letter-spacing: var(--tracking-hero);    font-family: var(--font-sf-pro-display); }

/* ─── Números financieros ─── */
.financial-number {
  font-family: var(--font-courier-new);
  font-variant-numeric: tabular-nums lining-nums;
  font-feature-settings: "numr";
  letter-spacing: -0.07em;
}

/* ─── Grid dashboard ─── */
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: var(--spacing-16);
}

/* ─── Componentes globales ─── */
.premium-card,
.mercury-panel {
  border: 1px solid var(--border-soft);
  background: var(--bg-card);
  border-radius: var(--radius-cards);
  box-shadow: none;
  backdrop-filter: none;
}

[class*="shadow"] {
  box-shadow: none !important;
}

.mercury-button {
  border: 1px solid var(--border-soft);
  background: transparent;
  color: var(--text-primary);
  border-radius: var(--radius-buttons);
  box-shadow: none;
  padding: 10px 20px;
  font-size: var(--text-body);
  font-weight: var(--font-weight-semibold);
  letter-spacing: var(--tracking-body);
  transition: opacity 100ms ease;
  cursor: pointer;
}

.mercury-button:hover {
  opacity: 0.85;
}

.mercury-button-primary {
  border: none;
  background: var(--primary);
  color: var(--on-primary);
  border-radius: var(--radius-buttons);
  box-shadow: none;
  padding: 10px 20px;
  font-size: var(--text-body);
  font-weight: var(--font-weight-semibold);
  letter-spacing: var(--tracking-body);
  transition: opacity 100ms ease;
  cursor: pointer;
}

.mercury-button-primary:hover {
  opacity: 0.85;
}

input,
select,
textarea {
  color-scheme: light dark;
}

table {
  border-collapse: separate;
  border-spacing: 0;
}

::selection {
  background: rgba(0, 113, 227, 0.3);
  color: var(--text-primary);
}

@media (max-width: 1100px) {
  .dashboard-grid {
    grid-template-columns: repeat(6, minmax(0, 1fr));
  }
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: .01ms !important;
    transition-duration: .01ms !important;
  }
}

::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--bg-surface);
}

::-webkit-scrollbar-thumb {
  background: var(--border-strong);
  border-radius: 99px;
}

/* ─── Animaciones de precio ─── */
.flash-up {
  animation: flash-up 300ms ease-out forwards;
}

.flash-down {
  animation: flash-down 300ms ease-out forwards;
}

@keyframes flash-up {
  0%   { background-color: rgba(0, 129, 99, .18); }
  100% { background-color: transparent; }
}

@keyframes flash-down {
  0%   { background-color: rgba(238, 37, 38, .16); }
  100% { background-color: transparent; }
}

.live-dot {
  animation: live-pulse 2s ease-in-out infinite;
}

@keyframes live-pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: .3; }
}
```

- [ ] **Step 2: Verificar que el archivo se guardó correctamente**

Comprobar que el archivo tiene los tres bloques: `:root`, `[data-theme="dark"]`, `[data-theme="light"]`.

- [ ] **Step 3: Commit**

```bash
git add apps/desktop/src/index.css
git commit -m "style: replace CSS tokens with Apple design system, add dark/light theme blocks"
```

---

## Task 2: Tailwind Config — Mapeo a CSS Variables

**Files:**
- Modify: `apps/desktop/tailwind.config.ts`

**Interfaces:**
- Consumes: Variables CSS de Task 1 — `var(--bg-app)`, `var(--bg-card)`, `var(--text-primary)`, `var(--text-secondary)`, `var(--border-soft)`, `var(--primary)`, `var(--positive)`, `var(--negative)`, `var(--warning)`, `var(--info)`, `var(--accent)`, `var(--on-primary)`, `var(--hairline-dark)`, `var(--divider-soft)`, `var(--bg-sidebar)`, `var(--bg-surface)`, `var(--bg-card-elevated)`, `var(--bg-interactive)`, `var(--text-muted)`, `var(--border-strong)`
- Produces: Clases Tailwind que adoptan el tema automáticamente. Los nombres existentes en TSX (`text-stone`, `bg-bone-cream`, `text-ink`, `text-on-dark`, etc.) siguen funcionando pero ahora apuntan a los nuevos tokens

- [ ] **Step 1: Reemplazar `tailwind.config.ts` con el nuevo contenido**

```typescript
import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        /* ── Paleta Apple nombrada ── */
        obsidian:      "#1d1d1f",
        "frost-white": "#f5f5f7",
        "pure-black":  "#000000",
        "paper-white": "#ffffff",
        carbon:        "#111111",
        platinum:      "#86868b",
        graphite:      "#333336",
        "silver-mist": "#cccccc",
        smoke:         "#424245",
        "apple-blue":  "#0071e3",
        "link-blue":   "#0066cc",
        "halo-blue":   "#2997ff",
        "signal-orange": "#f56900",
        "iris-violet": "#8668ff",
        "reef-teal":   "#00a1b3",

        /* ── Tokens semánticos → CSS vars (responden al tema) ── */
        "bg-app":          "var(--bg-app)",
        "bg-sidebar":      "var(--bg-sidebar)",
        "bg-surface":      "var(--bg-surface)",
        "bg-card":         "var(--bg-card)",
        "bg-card-elevated":"var(--bg-card-elevated)",
        "bg-interactive":  "var(--bg-interactive)",
        "border-soft":     "var(--border-soft)",
        "border-strong":   "var(--border-strong)",
        "divider-soft":    "var(--divider-soft)",
        "hairline-dark":   "var(--hairline-dark)",

        /* ── Aliases de compatibilidad (nombres antiguos → nuevos tokens) ── */
        /* Estos mantienen funcionando los TSX existentes sin cambios */
        ink:           "var(--text-primary)",
        charcoal:      "var(--text-secondary)",
        stone:         "var(--text-secondary)",
        mute:          "var(--text-muted)",
        "bone-cream":  "var(--bg-app)",
        "canvas-dark": "var(--bg-app)",
        "surface-deep":"var(--bg-surface)",
        "surface-elevated": "var(--bg-card-elevated)",
        "surface-card":"var(--bg-card)",

        primary: {
          DEFAULT: "var(--primary)",
          bright:  "var(--primary)",
        },
        "on-primary": "var(--on-primary)",
        "on-dark": {
          DEFAULT: "var(--text-primary)",
          mute:    "var(--text-secondary)",
        },
        hairline: {
          dark: "var(--hairline-dark)",
          soft: "var(--divider-soft)",
        },
        accent: {
          teal:    "var(--positive)",
          danger:  "var(--negative)",
          warning: "var(--warning)",
          yellow:  "var(--accent)",
        },

        /* ── Colores funcionales directos ── */
        "ember-orange": "#ff3d00",
      },

      fontFamily: {
        sans:    ["'SF Pro Text'", "Inter", "ui-sans-serif", "system-ui", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        display: ["'SF Pro Display'", "Inter", "ui-sans-serif", "system-ui", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        mono:    ["'Courier New'", "ui-monospace", "monospace"],
      },

      fontSize: {
        /* Escala DESIGN.md */
        "caption":    ["10px", { lineHeight: "1.83", letterSpacing: "-0.37px" }],
        "body":       ["14px", { lineHeight: "1.43", letterSpacing: "-0.22px" }],
        "heading-sm": ["19px", { lineHeight: "1.21", letterSpacing: "-0.28px", fontWeight: "600" }],
        "heading":    ["24px", { lineHeight: "1.17", letterSpacing: "-0.24px", fontWeight: "600" }],
        "heading-lg": ["32px", { lineHeight: "1.14", letterSpacing: "-0.32px", fontWeight: "700" }],
        "display":    ["56px", { lineHeight: "1.07", letterSpacing: "-0.84px", fontWeight: "700" }],
        "hero":       ["80px", { lineHeight: "1.05", letterSpacing: "-0.24px", fontWeight: "700" }],

        /* Aliases de compatibilidad (mantienen TSX existentes) */
        "display-lg": ["56px", { lineHeight: "1.07", letterSpacing: "-0.84px", fontWeight: "700" }],
        "heading-md": ["32px", { lineHeight: "1.14", letterSpacing: "-0.32px", fontWeight: "700" }],
        "body-md":    ["17px", { lineHeight: "1.47", letterSpacing: "-0.22px" }],
        "body-sm":    ["14px", { lineHeight: "1.43", letterSpacing: "-0.22px" }],
        "button-md":  ["14px", { lineHeight: "1.43", letterSpacing: "-0.22px", fontWeight: "600" }],
      },

      borderRadius: {
        sm:    "10px",
        md:    "10px",
        lg:    "10px",
        xl:    "10px",
        "2xl": "28px",
        "3xl": "28px",
        "4xl": "36px",
        full:  "980px",
      },

      spacing: {
        xs:   "8px",
        sm:   "8px",
        md:   "16px",
        lg:   "24px",
        xl:   "28px",
        "2xl":"32px",
        "3xl":"48px",
        "4xl":"64px",
        "5xl":"80px",
        "8":  "8px",
        "16": "16px",
        "24": "24px",
      },
    },
  },
  plugins: [],
} satisfies Config;
```

- [ ] **Step 2: Arrancar el servidor de desarrollo y verificar visualmente**

```bash
cd apps/desktop && npm run dev
```

Verificar en el navegador:
- El fondo de la app es negro puro (`#000000`)
- Los textos principales aparecen en blanco (`#f5f5f7`)
- Las tarjetas aparecen en obsidian (`#1d1d1f`)
- No hay errores de compilación en la consola de Vite

- [ ] **Step 3: Commit**

```bash
git add apps/desktop/tailwind.config.ts
git commit -m "style: map tailwind colors to CSS variables for theme switching"
```

---

## Task 3: Theme Init + Hook

**Files:**
- Modify: `apps/desktop/src/main.tsx`
- Create: `apps/desktop/src/lib/useTheme.ts`

**Interfaces:**
- Consumes: `localStorage` clave `'theme'`, `document.documentElement` para `data-theme`
- Produces:
  - `main.tsx` aplica el tema antes del primer render (sin flash)
  - `useTheme()` → `{ theme: 'dark' | 'light', setTheme: (t: 'dark' | 'light') => void }`

- [ ] **Step 1: Modificar `main.tsx` para inicializar tema antes del render**

Reemplazar el contenido completo de `apps/desktop/src/main.tsx`:

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./index.css";

// Aplicar tema antes del primer render para evitar flash
const savedTheme = localStorage.getItem("theme") || "dark";
document.documentElement.setAttribute("data-theme", savedTheme);

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
```

- [ ] **Step 2: Crear `apps/desktop/src/lib/useTheme.ts`**

```typescript
type Theme = "dark" | "light";

export function useTheme() {
  const theme = (document.documentElement.getAttribute("data-theme") as Theme) || "dark";

  function setTheme(next: Theme) {
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
  }

  return { theme, setTheme };
}
```

- [ ] **Step 3: Verificar que el hook no causa errores de compilación**

```bash
cd apps/desktop && npx tsc --noEmit
```

Resultado esperado: sin errores de TypeScript.

- [ ] **Step 4: Commit**

```bash
git add apps/desktop/src/main.tsx apps/desktop/src/lib/useTheme.ts
git commit -m "feat: add theme initialization and useTheme hook"
```

---

## Task 4: RootLayout — Sidebar y Nav

**Files:**
- Modify: `apps/desktop/src/app/layout/RootLayout.tsx`

**Interfaces:**
- Consumes: `useTheme()` de `@/lib/useTheme` — no se usa directamente en el layout, el tema se aplica vía CSS vars
- Produces: Layout visual con sidebar obsidian, nav items sin colores por ítem, header 56px, footer sin barra naranja

- [ ] **Step 1: Reemplazar el contenido de `RootLayout.tsx`**

```tsx
import {
  Activity,
  ArrowLeftRight,
  BarChart2,
  Bot,
  CalendarDays,
  Globe,
  LayoutDashboard,
  Lightbulb,
  Settings,
  Target,
  TrendingDown,
  Upload,
  Wallet,
} from "lucide-react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { getCopilotContext } from "@/features/assistant/contextualCopilot";

interface NavItem {
  to: string;
  icon: typeof LayoutDashboard;
  label: string;
  end?: boolean;
}

const navItems: NavItem[] = [
  { to: "/",             icon: LayoutDashboard, label: "Resumen",      end: true },
  { to: "/spending",     icon: TrendingDown,    label: "Gastos" },
  { to: "/transactions", icon: ArrowLeftRight,  label: "Movimientos" },
  { to: "/accounts",     icon: Wallet,          label: "Cuentas" },
  { to: "/imports",      icon: Upload,          label: "Importar" },
  { to: "/investments",  icon: BarChart2,       label: "Inversiones" },
  { to: "/economy",      icon: Globe,           label: "Economia" },
  { to: "/markets",      icon: Activity,        label: "Mercados" },
  { to: "/goals",        icon: Target,          label: "Objetivos" },
  { to: "/planificacion",icon: CalendarDays,    label: "Planificacion" },
  { to: "/insights",     icon: Lightbulb,       label: "Insights" },
  { to: "/assistant",    icon: Bot,             label: "Asistente" },
  { to: "/settings",     icon: Settings,        label: "Ajustes" },
];

export default function RootLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const copilot = getCopilotContext(location.pathname);
  const showCopilot = location.pathname !== "/assistant" && location.pathname !== "/settings";

  const copilotPanel = showCopilot ? (
    <aside className="hidden w-[344px] shrink-0 overflow-y-auto border-l border-[var(--border-soft)] bg-[var(--bg-app)] p-5 xl:block">
      <div className="sticky top-5 rounded-[28px] border border-[var(--border-soft)] bg-[var(--bg-card)] p-5">
        <div className="flex items-start gap-3">
          <span className="grid h-9 w-9 shrink-0 place-items-center rounded-[10px] bg-[var(--primary)] text-white">
            <Bot size={16} />
          </span>
          <div className="min-w-0">
            <p
              className="font-semibold text-[var(--text-primary)]"
              style={{ fontSize: "14px", lineHeight: "1.43", letterSpacing: "-0.22px" }}
            >
              Copiloto contextual
            </p>
            <p
              className="mt-1 text-[var(--text-secondary)]"
              style={{ fontSize: "12px", lineHeight: "1.43" }}
            >
              {copilot.module} - {copilot.data_status}
            </p>
          </div>
        </div>
        <div className="mt-3 flex flex-wrap gap-1.5">
          {copilot.visible_metrics.slice(0, 4).map((metric) => (
            <span
              key={metric}
              className="rounded-[10px] border border-[var(--border-soft)] bg-[var(--bg-card-elevated)] px-2 py-1 text-[var(--text-secondary)]"
              style={{ fontSize: "11px" }}
            >
              {metric}
            </span>
          ))}
        </div>
        <div className="mt-3 grid gap-2">
          {copilot.suggestedQuestions.slice(0, 2).map((question) => (
            <button
              key={question}
              onClick={() => navigate("/assistant", { state: { prompt: question, context: copilot } })}
              className="rounded-[10px] border border-[var(--border-soft)] bg-[var(--bg-interactive)] px-3 py-2 text-left text-[var(--text-primary)] hover:border-[var(--border-strong)]"
              style={{ fontSize: "12px", lineHeight: "1.5" }}
            >
              {question}
            </button>
          ))}
        </div>
      </div>
    </aside>
  ) : null;

  return (
    <div className="flex h-full flex-col lg:flex-row" style={{ background: "var(--bg-app)", color: "var(--text-primary)" }} data-app-ready="true">
      {/* Sidebar desktop */}
      <aside className="hidden w-[192px] flex-shrink-0 overflow-y-auto px-3 py-6 lg:block" style={{ background: "var(--bg-sidebar)" }}>
        <div className="mb-6 px-3">
          <p
            className="font-semibold text-[var(--color-frost-white)]"
            style={{ fontFamily: "var(--font-sf-pro-display)", fontSize: "19px", lineHeight: "1.21", letterSpacing: "-0.28px" }}
          >
            Financial OS
          </p>
          <p className="mt-1 text-[var(--color-platinum)]" style={{ fontSize: "12px", lineHeight: "1.43" }}>
            Local finance system
          </p>
        </div>

        <nav aria-label="Navegacion principal" className="space-y-0.5">
          {navItems.map(({ to, icon: Icon, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                [
                  "flex items-center gap-2.5 rounded-[10px] px-3 py-2.5 transition-colors duration-100",
                  isActive
                    ? "bg-[var(--color-graphite)] text-[var(--color-frost-white)]"
                    : "text-[var(--color-platinum)] hover:bg-[rgba(245,245,247,0.06)] hover:text-[var(--color-frost-white)]",
                ].join(" ")
              }
            >
              <Icon size={14} />
              <span style={{ fontSize: "14px", lineHeight: "1.43", letterSpacing: "-0.22px" }}>{label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Nav mobile */}
      <div
        className="border-b px-4 py-3 lg:hidden"
        style={{ background: "var(--bg-sidebar)", borderColor: "var(--border-soft)" }}
      >
        <div className="flex items-center justify-between gap-4">
          <div>
            <p
              className="text-[var(--color-frost-white)]"
              style={{ fontFamily: "var(--font-sf-pro-display)", fontSize: "19px", lineHeight: "1.21", letterSpacing: "-0.28px", fontWeight: 600 }}
            >
              Financial OS
            </p>
            <p className="mt-1 text-[var(--color-platinum)]" style={{ fontSize: "12px" }}>
              Local finance system
            </p>
          </div>
          <span className="text-[var(--color-platinum)]" style={{ fontSize: "13px", letterSpacing: "-0.16px" }}>
            Local-first
          </span>
        </div>
        <nav aria-label="Navegacion principal movil" className="mt-3 flex gap-2 overflow-x-auto pb-1">
          {navItems.map(({ to, icon: Icon, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                [
                  "flex min-w-[100px] shrink-0 items-center gap-2 rounded-[10px] border px-3 py-2",
                  isActive
                    ? "border-[var(--color-graphite)] bg-[var(--color-graphite)] text-[var(--color-frost-white)]"
                    : "border-transparent text-[var(--color-platinum)] hover:bg-[rgba(245,245,247,0.06)]",
                ].join(" ")
              }
            >
              <Icon size={13} />
              <span className="truncate" style={{ fontSize: "12px", letterSpacing: "-0.22px" }}>
                {label}
              </span>
            </NavLink>
          ))}
        </nav>
      </div>

      {/* Contenido principal */}
      <div className="flex min-h-0 min-w-0 flex-1 flex-col" style={{ background: "var(--bg-app)" }}>
        <header
          className="hidden h-14 shrink-0 items-center justify-between px-6 lg:flex"
          style={{ borderBottom: "1px solid var(--border-soft)", color: "var(--text-secondary)" }}
        >
          <span style={{ fontSize: "17px", lineHeight: "1.21", letterSpacing: "-0.22px" }}>Private command center</span>
          <span style={{ fontSize: "17px", lineHeight: "1.21", letterSpacing: "-0.22px" }}>Local-first wealth workspace</span>
        </header>
        <div className="flex min-h-0 flex-1">
          <main className="flex-1 min-w-0 overflow-y-auto">
            <Outlet />
          </main>
          {copilotPanel}
        </div>
        <div style={{ height: "1px", width: "100%", background: "var(--border-soft)" }} />
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verificar visualmente en el navegador**

Con el dev server activo, navegar por la app y comprobar:
- Sidebar muestra fondo obsidian (`#1d1d1f`) en ambos temas
- Nav items sin colores de fondo por ítem
- Nav activo con fondo `#333336` y texto frost-white
- Header de 56px (h-14) con borde inferior sutil
- Pie de página: línea de 1px `var(--border-soft)` en lugar de barra naranja

- [ ] **Step 3: Commit**

```bash
git add apps/desktop/src/app/layout/RootLayout.tsx
git commit -m "style: apply Apple design system to RootLayout sidebar and nav"
```

---

## Task 5: Theme Toggle en SettingsPage

**Files:**
- Modify: `apps/desktop/src/features/settings/SettingsPage.tsx`

**Interfaces:**
- Consumes: `useTheme()` de `@/lib/useTheme` — `{ theme: 'dark' | 'light', setTheme: (t) => void }`
- Produces: Sección "Apariencia" en SettingsPage con dos cards seleccionables que cambian el tema en tiempo real

- [ ] **Step 1: Añadir import de useTheme en `SettingsPage.tsx`**

Añadir al bloque de imports existente (línea ~1, después de los imports actuales):

```tsx
import { useTheme } from "@/lib/useTheme";
```

- [ ] **Step 2: Añadir hook en el cuerpo del componente**

Dentro de `SettingsPage()`, después de la línea `const lastBackup = backups[0];` (línea ~73), añadir:

```tsx
const { theme, setTheme } = useTheme();
```

- [ ] **Step 3: Reemplazar el bloque de fila "Tema" en la sección Preferencias**

Localizar y reemplazar el bloque existente del tema (líneas ~115-118):

```tsx
{/* Antes: */}
<div className="p-xl flex items-center justify-between gap-6">
  <div><p className="text-body-md text-on-dark">Tema</p><p className="text-caption text-stone mt-xs">Modo visual de la aplicacion</p></div>
  <span className="rounded-lg bg-white/[.045] px-3 py-2 text-body-sm text-stone">Dark Premium Mercury</span>
</div>
```

Reemplazar con:

```tsx
{/* Después: */}
<div className="p-xl">
  <p className="text-body-md text-on-dark mb-1">Apariencia</p>
  <p className="text-caption text-stone mb-3">Elige el modo visual de la aplicacion</p>
  <div className="flex gap-3">
    {(["dark", "light"] as const).map((t) => (
      <button
        key={t}
        onClick={() => setTheme(t)}
        className="flex-1 rounded-[28px] p-4 text-left transition-all"
        style={{
          border: theme === t ? "2px solid #0071e3" : "1px solid var(--border-soft)",
          background: t === "dark" ? "#000000" : "#f5f5f7",
          cursor: "pointer",
        }}
      >
        <div
          className="mb-2 h-8 rounded-[10px]"
          style={{ background: t === "dark" ? "#1d1d1f" : "#ffffff", border: "1px solid", borderColor: t === "dark" ? "#333336" : "#e5e5e5" }}
        />
        <p
          style={{
            fontSize: "12px",
            fontWeight: 600,
            letterSpacing: "-0.22px",
            color: t === "dark" ? "#f5f5f7" : "#1d1d1f",
          }}
        >
          {t === "dark" ? "Oscuro" : "Claro"}
        </p>
      </button>
    ))}
  </div>
</div>
```

- [ ] **Step 4: Verificar en el navegador**

Navegar a `/settings`:
- Ver la sección "Apariencia" con dos cards: "Oscuro" y "Claro"
- Card activa tiene borde azul (`#0071e3`)
- Hacer clic en "Claro" → la app entera cambia a tema claro instantáneamente
- Recargar la página → el tema claro persiste
- Hacer clic en "Oscuro" → vuelve al tema oscuro
- Recargar → persiste oscuro

- [ ] **Step 5: Commit**

```bash
git add apps/desktop/src/features/settings/SettingsPage.tsx
git commit -m "feat: add light/dark theme toggle in Settings > Apariencia"
```

---

## Verificación final

Con todos los tasks completados, hacer un recorrido visual completo:

- [ ] Navegar por todas las páginas en **tema oscuro**: Resumen, Gastos, Movimientos, Inversiones, Mercados, Asistente
- [ ] Cambiar a **tema claro** desde Settings y repetir el recorrido
- [ ] Comprobar que no hay elementos con fondo bone-cream hardcodeado (`#f4e9e1`) visible
- [ ] Comprobar que las tarjetas tienen `border-radius: 28px`
- [ ] Comprobar que no hay `box-shadow` visible en ninguna tarjeta
- [ ] Comprobar que el botón "Crear backup" en Settings aparece en Apple Blue
- [ ] Comprobar que la barra inferior del layout es una línea fina, no la barra naranja anterior
