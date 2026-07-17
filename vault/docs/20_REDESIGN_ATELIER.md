# 20 — Rediseño "Atelier" (Propuesta C) · Especificación de implementación

> **Para el agente implementador (Opus 4.8):** este documento es la fuente de verdad del rediseño.
> Fue aprobado por el usuario el 2026-07-12 tras una propuesta con tres direcciones; eligió la C ("Atelier").
> Léelo completo antes de tocar código. Las fases están ordenadas por dependencia: no saltes fases.

---

## 0. Contexto y objetivo

**Qué es la app:** AI Financial OS, sistema financiero personal local-first (Tauri + React 18 + TypeScript + Tailwind 3 + Recharts; backend FastAPI). Frontend en `apps/desktop/`.

**Objetivo del rediseño:** convertir la UI actual (oscura, H1 gigantes de 80px, Courier New en cifras, sin sombras ni jerarquía de superficie) en un producto de consumo premium estilo Apple **light-first**: lienzo claro, tarjetas blancas con sombra suave, una tarjeta hero grafito con el patrimonio como protagonista, insights narrados, y motion con física (springs, odometer).

**Decisión que supersede una restricción previa:** la restricción histórica "Mantener estilo Dark Premium" queda **sustituida** por decisión explícita del usuario (2026-07-12): la app pasa a ser **light-first**, con tema oscuro plenamente soportado y cuidado (no un invertido automático). El resto de restricciones del proyecto siguen vigentes (ver §1).

**Principio de producto que el rediseño debe materializar** (de `docs/01_PRODUCT_VISION.md`):
Resumen → Explicación → Detalle → Acción. Cada pantalla responde: qué pasa, por qué importa, qué datos lo explican, qué puedo hacer.

---

## 1. Reglas de trabajo obligatorias

1. **Idioma:** toda la UI en español. Este rediseño incluye corregir textos en inglés (ver §7.8).
2. **Sin commits automáticos:** puedes hacer stage (`git add`), pero **nunca** `git commit` sin confirmación explícita del usuario.
3. **No ejecutar tests sin permiso explícito** del usuario.
4. **Verificación visual obligatoria:** tras cada fase que cambie UI, ejecuta `npm run ux:snapshots:headed` desde `apps/desktop/` y revisa las capturas en ambos temas antes de dar la fase por cerrada.
5. **No sobrecargar la UI:** si una instrucción de este documento entra en conflicto con la claridad, gana la claridad. Menos elementos, mejor ejecutados.
6. **Dependencias:** la única librería nueva permitida es `framer-motion`. No introducir shadcn/ui ni ninguna otra librería de componentes en este rediseño; se mantienen los componentes propios existentes. Recharts sigue siendo la librería de gráficos.
7. **Compatibilidad:** `tailwind.config.ts` expone aliases de compatibilidad (`ink`, `stone`, `premium-card`, etc.) usados por decenas de TSX. **No los elimines**: cambia lo que apuntan (los CSS vars), no los nombres. Así el retema se propaga sin tocar cada archivo.
8. **Accesibilidad:** respetar `prefers-reduced-motion` (ya hay un bloque en `index.css`; framer-motion debe usar `<MotionConfig reducedMotion="user">`). Mantener los `focus-visible` existentes. Contraste AA mínimo en ambos temas.

---

## 2. Archivos clave (estado actual)

| Archivo | Qué contiene hoy | Qué le pasa en el rediseño |
|---|---|---|
| `src/index.css` | Tokens CSS (paleta Apple, temas dark/light), `.premium-card`, `.mercury-button*`, `.financial-number` (Courier New), `box-shadow: none !important` | Reescritura de tokens y componentes globales (Fase 1) |
| `tailwind.config.ts` | Mapeo tokens→Tailwind, aliases compat, `fontFamily.mono: Courier New`, radius 10/28/36 | Ajustes de fuentes, radius y sombras (Fase 1) |
| `src/main.tsx` | Tema por defecto `"dark"` | Pasa a `"light"` (Fase 1) |
| `src/lib/useTheme.ts` | Hook de tema por `data-theme` + localStorage | Sin cambios |
| `src/app/layout/RootLayout.tsx` | Sidebar SIEMPRE oscuro (colores hardcodeados `frost-white`/`platinum`), header superior de 56px con "Centro de control privado", popover copiloto | Sidebar tokenizado y translúcido, header fusionado (Fase 2) |
| `src/app/layout/ComienzaWidget.tsx` | Checklist de onboarding fijo en sidebar | Colapsa a píldora de progreso (Fase 2) |
| `src/components/ui/Dashboard.tsx` | `PageHeader` (H1 80px), `KpiCard`, `ChartCard`, `EmptyState`, `ErrorState`, `LoadingState`, `DataSourceBadge` | `PageHeader` compacto, `KpiCard` con delta, `EmptyState` con preview (Fases 2, 3, 6) |
| `src/features/dashboard/DashboardPage.tsx` | 4 KPI planas + BalanceGeneralPanel colapsado + secciones | Hero de patrimonio + KPI con deltas + fila de insights (Fase 3) |
| `src/components/ui/MetricCard.tsx` | Tarjeta métrica alternativa (usada en otras páginas) | Solo retema vía tokens; unificar visualmente con KpiCard |
| Páginas de features (`src/features/*/…Page.tsx`) | Todas usan `PageHeader` + `premium-card` | Heredan el retema; ajustes puntuales en Fase 6 |

---

## 3. Sistema de tokens (Fase 1 — la fase más importante)

Reescribir los bloques de tema de `src/index.css`. Los **nombres** de las variables no cambian (compatibilidad); cambian los **valores** y se añaden las nuevas (`--bg-hero-*`, `--shadow-*`, `--bg-sidebar-active`).

### 3.1 Tema claro (nuevo default)

```css
[data-theme="light"] {
  --bg-app: #F2F3F5;                      /* lienzo, ligeramente frío */
  --bg-sidebar: rgba(255, 255, 255, 0.72); /* material translúcido, requiere backdrop-filter */
  --bg-sidebar-active: #FFFFFF;            /* item activo: píldora blanca */
  --bg-surface: #FFFFFF;
  --bg-card: #FFFFFF;
  --bg-card-elevated: #F5F5F7;
  --bg-interactive: #F0F0F2;
  --bg-hero-from: #1D1D1F;                 /* tarjeta hero grafito */
  --bg-hero-to: #2C2C30;
  --text-primary: #1D1D1F;
  --text-secondary: #6E6E73;
  --text-muted: rgba(29, 29, 31, 0.45);
  --text-on-hero: #F5F5F7;
  --text-on-hero-secondary: #A1A1A6;
  --border-soft: #E4E4E7;
  --border-strong: #D2D2D7;
  --divider-soft: rgba(29, 29, 31, 0.08);
  --hairline-dark: #E4E4E7;
  --primary: #0071E3;
  --positive: #059669;
  --negative: #DC2626;
  --warning: #D97706;
  --shadow-card: 0 1px 3px rgba(0, 0, 0, 0.06);
  --shadow-card-hover: 0 4px 12px rgba(0, 0, 0, 0.09);
  --shadow-elevated: 0 8px 24px rgba(0, 0, 0, 0.10);
  --shadow-hero: 0 12px 32px rgba(29, 29, 31, 0.18);
}
```

### 3.2 Tema oscuro (se conserva, refinado — NO negro puro)

```css
[data-theme="dark"] {
  --bg-app: #111113;
  --bg-sidebar: rgba(28, 28, 30, 0.72);
  --bg-sidebar-active: #2C2C2E;
  --bg-surface: #1C1C1E;
  --bg-card: #1C1C1E;
  --bg-card-elevated: #2C2C2E;
  --bg-interactive: #2C2C2E;
  --bg-hero-from: #2C2C2E;                 /* en oscuro el hero se distingue por elevación, no por inversión */
  --bg-hero-to: #3A3A3C;
  --text-primary: #F5F5F7;
  --text-secondary: #98989D;
  --text-muted: rgba(245, 245, 247, 0.45);
  --text-on-hero: #F5F5F7;
  --text-on-hero-secondary: #A1A1A6;
  --border-soft: #2C2C2E;
  --border-strong: #3A3A3C;
  --divider-soft: rgba(245, 245, 247, 0.08);
  --hairline-dark: #2C2C2E;
  --primary: #0A84FF;                      /* paleta Apple dark */
  --positive: #30D158;
  --negative: #FF453A;
  --warning: #FF9F0A;
  --shadow-card: 0 1px 3px rgba(0, 0, 0, 0.35);
  --shadow-card-hover: 0 4px 12px rgba(0, 0, 0, 0.45);
  --shadow-elevated: 0 8px 24px rgba(0, 0, 0, 0.5);
  --shadow-hero: 0 12px 32px rgba(0, 0, 0, 0.5);
}
```

Notas:
- `--primary`, `--positive`, `--negative`, `--warning` **salen del bloque `:root` compartido** y pasan a definirse por tema (hoy están compartidos; los valores dark y light deben diferir).
- El delta positivo sobre el hero grafito usa `#6EE7B7` (definir `--positive-on-hero: #6EE7B7` en ambos temas).

### 3.3 Tipografía y cifras

En `index.css`:

1. **Eliminar `font-feature-settings: "numr"`** de `html/body` y de `.financial-number` (la feature "numr" convierte dígitos en numeradores de fracción — es un bug tipográfico, no un estilo).
2. Redefinir `.financial-number`:
   ```css
   .financial-number {
     font-family: var(--font-sf-pro-display);
     font-variant-numeric: tabular-nums lining-nums;
     letter-spacing: -0.02em;
     font-weight: 650;
   }
   ```
   Courier New desaparece de la app. En `tailwind.config.ts`, `fontFamily.mono` pasa a `["'SF Mono'", "ui-monospace", "Consolas", "monospace"]` (solo se usará para código/atajos, no para dinero).
3. Escala de página (sustituye el uso de `hero`/`display` en títulos de página):
   - Título de página: 24px / 600 / tracking -0.4px (ya existe como `text-heading`).
   - Cifra hero (patrimonio): 40px / 700 / tracking -1px → añadir token `--text-hero-value: 40px`.
   - Cifra KPI: 22px / 650.
   - Los tamaños `display` (56) y `hero` (80) se conservan en la escala pero **dejan de usarse en `PageHeader`**.

### 3.4 Superficie, radios y sombras

1. **Eliminar el bloque `[class*="shadow"] { box-shadow: none !important; }`** de `index.css`.
2. `.premium-card` / `.mercury-panel`:
   ```css
   border: 1px solid var(--border-soft);
   background: var(--bg-card);
   border-radius: 16px;
   box-shadow: var(--shadow-card);
   transition: box-shadow 150ms ease, transform 150ms ease;
   ```
3. Radios en `tailwind.config.ts`: `sm: 8px, md: 10px, lg: 12px, xl: 16px, 2xl: 20px, 3xl: 24px, full: 980px`. Los botones dejan la píldora de 36px: `.mercury-button*` pasan a `border-radius: 12px`.
4. Botón primario: añade `box-shadow: 0 1px 2px rgba(0,113,227,.35)` y hover `filter: brightness(1.06)` en lugar de `opacity: .85`. Estado activo `transform: scale(.98)`.

### 3.5 Verificación de Fase 1

- Arranca la app: debe verse en claro por defecto (`main.tsx` con `localStorage.getItem("theme") || "light"`).
- Cambia a oscuro en Ajustes: ninguna pantalla debe quedar ilegible.
- Busca restos: `grep -r "Courier" src/` debe devolver 0; `grep -rn "numr" src/` debe devolver 0; `grep -n "!important" src/index.css` no debe incluir box-shadow.
- `npm run ux:snapshots:headed` y revisar.

---

## 4. Chrome de aplicación (Fase 2)

### 4.1 `RootLayout.tsx` — sidebar

- Sustituir TODOS los colores hardcodeados (`--color-frost-white`, `--color-platinum`, `--color-graphite`, `rgba(245,245,247,…)`) por tokens semánticos (`--text-primary`, `--text-secondary`, `--bg-sidebar-active`, `--divider-soft`). El sidebar debe responder al tema.
- Estilo: `background: var(--bg-sidebar); backdrop-filter: blur(20px) saturate(1.4); border-right: 1px solid var(--border-soft);`.
- Item activo: fondo `var(--bg-sidebar-active)`, `border-radius: 10px`, `box-shadow: var(--shadow-card)`, texto `var(--text-primary)` semibold. Inactivo: `var(--text-secondary)`.
- Renombrar "Dashboard" → **"Resumen"** (también la ruta puede quedarse en `/`, solo cambia el label).

### 4.2 `RootLayout.tsx` — header superior

- El header de 56px deja de mostrar el texto fijo "Centro de control privado". Pasa a mostrar: **título de la sección actual** (14px, semibold, `--text-primary`) a la izquierda — derivarlo de `navItems` + `location.pathname` — y a la derecha el botón del copiloto (se mantiene) más las acciones que hoy viven en los `PageHeader` cuando sea razonable moverlas.
- El divisor inferior de 1px al final del layout (línea 226 aprox.) se elimina; era un artefacto.

### 4.3 `PageHeader` (`src/components/ui/Dashboard.tsx`)

Reescribir manteniendo la firma (`eyebrow`, `title`, `description`, `actions`) para no romper llamadas:

```tsx
<header className="flex items-center justify-between gap-6 pb-6">
  <div className="min-w-0">
    <h1 className="text-heading text-[var(--text-primary)]">{title}</h1>
    {description && <p className="mt-1 text-[13px] text-[var(--text-secondary)]">{description}</p>}
  </div>
  {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
</header>
```

- El `eyebrow` **se ignora** (prop conservada como deprecated para no tocar ~15 call sites; puedes limpiarlos si sobra tiempo).
- Resultado: cada página recupera ~300px verticales.

### 4.4 `ComienzaWidget.tsx`

- Colapsar a una píldora compacta al pie del sidebar: icono anillo de progreso + "3/4" + label "Comienza". Al hacer clic abre popover con el checklist actual (reutilizar el contenido existente).
- Cuando esté 4/4 el widget desaparece definitivamente (persistir el dismissal como ya haga hoy, o en localStorage).

---

## 5. Dashboard "¿cómo voy?" (Fase 3)

Reestructurar `DashboardPage.tsx`:

### 5.1 Hero de patrimonio (componente nuevo `src/features/dashboard/components/NetWorthHero.tsx`)

- Tarjeta a ancho completo: `background: linear-gradient(160deg, var(--bg-hero-from), var(--bg-hero-to)); border-radius: 20px; box-shadow: var(--shadow-hero); padding: 24-28px;`.
- Izquierda: label "Patrimonio neto · {mes año}" (11-12px, `--text-on-hero-secondary`), cifra 40px/700 (`.financial-number`, `--text-on-hero`), delta "▲ +X € este mes · sin pasivos" en `--positive-on-hero`.
- Derecha: sparkline de área de los últimos 6 meses del patrimonio (Recharts `AreaChart` mini, sin ejes, stroke `#6EE7B7`, fill degradado a transparente, punto final destacado).
- Datos: usar el hook de net worth existente (`src/lib/hooks/useNetWorth.ts`); si no hay histórico suficiente, ocultar el sparkline y mostrar solo la cifra (nunca datos inventados).
- La cifra hace **count-up** al montar (ver §8).

### 5.2 Fila de KPI (3 tarjetas, no 4)

- "Gastos del mes" con delta vs media de los últimos meses; "Ahorro neto" con tasa de ahorro; "Inversiones" con nº posiciones y retorno. El dato "Balance total" ya no se repite (vive en el hero).
- `KpiCard` gana soporte real de `delta` (ya existe la prop) — calcular deltas con los datos de `useOverview`/`useTransactions` disponibles; si el backend no da el dato comparativo, mostrar el hint actual sin inventar.

### 5.3 Fila de insights narrados (componente nuevo `InsightStrip.tsx`)

- Tarjeta horizontal: icono ✦ en contenedor azul suave, texto de una línea con la parte clave en bold, CTA "Ver desglose →" a la derecha que navega al módulo correspondiente.
- Fuente: `useInsights()` (ya se consume en el dashboard). Mostrar máximo 2. Si no hay insights, la fila no se renderiza (sin placeholder).

### 5.4 Resto

- `BalanceGeneralPanel` pasa a estar **abierto por defecto**.
- Las secciones "Últimos movimientos", "Portafolio", "Objetivos" se mantienen, heredando el retema.

---

## 6. Estados vacíos y de carga (Fase 5)

- `EmptyState` gana prop opcional `preview?: ReactNode`: un mini-gráfico demo desaturado (opacidad .5, `pointer-events: none`, badge "Ejemplo") encima del título, para enseñar qué obtendrá el usuario. Aplicarlo en: Goals, Insights, Presupuestos (BudgetTab), Inversiones vacío.
- `LoadingState`: sustituir el spinner central por skeletons con la silueta real de la página (hero + kpis en dashboard; filas en tablas). Ya existe `CardSkeleton` en `DashboardPage` como patrón; generalizarlo a `src/components/ui/Skeleton.tsx`.

---

## 7. Pasada por módulos (Fase 6)

Cambios puntuales; todo lo demás lo cubre el retema de tokens:

1. **Movimientos (`TransactionsPage`)**: la barra de filtros se compacta a una fila (búsqueda + selects); los filtros avanzados (fechas, importes) pasan a un popover "Filtros". Las cifras de la tabla alinean a la derecha con `tabular-nums`. Chips de categoría con fondo suave (fondo `--bg-interactive`, texto `--text-secondary`).
2. **Gastos (`SpendingPage`)**: las barras de "Gasto por categoría" usan `--primary`; el pie chart y las barras de evolución adoptan una paleta coherente derivada del azul (no verde+violeta mezclados). Definir en un solo sitio (`src/lib/chartPalette.ts`) y usarla en todos los Recharts: `["#0071E3", "#5AC8FA", "#8E8E93", "#34C759", "#FF9F0A", "#AF52DE"]` (claro) con equivalentes dark (`#0A84FF`, `#64D2FF`, `#98989D`, `#30D158`, `#FF9F0A`, `#BF5AF2`).
3. **Inversiones (`InvestmentsPage`)**: las 3 tarjetas KPI (Valor/Aportado/Rentabilidad) reducen padding y añaden sparkline si hay histórico. El segmented control "Posiciones / Calidad de cartera" adopta estilo iOS: contenedor `--bg-interactive` con thumb blanco (o `--bg-card-elevated` en dark) y sombra.
4. **Mercados (`MarketsPage`)**: ya es la mejor pantalla; solo hereda tokens. Conservar `flash-up`/`flash-down` y `live-dot`.
5. **Economía (`EconomyPage`)**: corregir "Economia" → "Economía" en el título; las tarjetas indicador usan el nuevo `KpiCard` visual.
6. **Planificación**: los 4 tabs adoptan el mismo segmented control iOS que Inversiones; corregir "Planificacion" → "Planificación".
7. **Asistente / Ajustes**: heredan tokens. En Ajustes, el selector de tema muestra el claro como primera opción.
8. **Textos a corregir** (grep de cada uno): "Position Tracking" → "Seguimiento de posiciones"; "Portfolio desk" → "Cartera"; "Market intelligence" → "Inteligencia de mercado"; "Ledger financiero" → "Libro de movimientos"; "Dashboard" → "Resumen"; revisar tildes en todos los títulos.

---

## 8. Sistema de motion (Fase 4)

Instalar `framer-motion` (`npm i framer-motion` en `apps/desktop/`). Envolver la app en `<MotionConfig reducedMotion="user">` (en `App.tsx`).

| Interacción | Spec | Dónde |
|---|---|---|
| Transición de ruta | Fade + rise 6px, 180ms ease-out, sin animación de salida (evita lag percibido) | Wrapper en `RootLayout` `<main>` con `key=location.pathname` |
| Count-up de cifras | 600ms ease-out desde 0 (o desde el valor anterior si cambia el mes). `useSpring`/`animate` de framer-motion; formatear con `formatCurrency` en cada frame | Hero patrimonio, cifras KPI |
| Stagger de tarjetas | children `y: 8, opacity: 0 → 1`, delay 30ms por item, solo en el primer mount de la página | Fila KPI, grids de tarjetas |
| Stagger de filas de tabla | igual, delay 20ms, máximo 12 filas animadas (el resto aparece sin animar) | Movimientos, posiciones, mercados |
| Springs en paneles | `type: "spring", stiffness: 260, damping: 24` para dialogs/drawers (scale .96→1 + fade) | Modales de inversiones, drawer de gastos, popover copiloto |
| Hover de tarjeta | `box-shadow: var(--shadow-card-hover)` vía CSS transition 150ms (no JS) | `.premium-card` |
| Gráficos | Recharts con animación activada, 700ms ease-out, una sola vez por mount | Todos los charts |
| Cambio de dato en vivo | conservar `flash-up`/`flash-down` CSS existentes | Mercados |

**Regla:** nada de bounce en elementos de datos; los springs solo en superficies (paneles que entran/salen). Si una animación se percibe en cada navegación repetida, se limita al primer mount.

---

## 9. Orden de ejecución y criterios de aceptación

| Fase | Alcance | Criterio de cierre |
|---|---|---|
| 1 | Tokens (§3): index.css + tailwind.config.ts + main.tsx | App claro por defecto, oscuro legible, sin Courier/`numr`/`!important` de sombras. Snapshots OK |
| 2 | Chrome (§4): RootLayout + PageHeader + ComienzaWidget | Ninguna página con H1 de 80px; sidebar responde al tema; header único. Snapshots OK |
| 3 | Dashboard (§5): hero + KPIs + insights | El dashboard responde "¿cómo voy?" sin scroll en 1440×900. Snapshots OK |
| 4 | Motion (§8) | Transiciones perceptibles pero no intrusivas; `prefers-reduced-motion` las desactiva |
| 5 | Estados vacíos y skeletons (§6) | Goals/Insights/Presupuestos vacíos enseñan preview |
| 6 | Pasada por módulos (§7) | Textos en español correcto; paleta de charts unificada; segmented controls consistentes |

**Al final de todo:** `npm run ux:snapshots:headed`, revisar las ~21 capturas en ambos temas, y presentar al usuario un resumen con capturas antes/después. No hacer commit sin su confirmación.

## 10. Qué NO hacer

- No añadir cinta de mercado ni línea de comandos (eran de las propuestas A/B descartadas).
- No tocar el backend ni los contratos de API.
- No renombrar rutas, hooks ni tipos; esto es un rediseño de presentación.
- No eliminar los aliases de compatibilidad de Tailwind.
- No introducir datos ficticios en producción para rellenar el hero/insights: si falta el dato, se oculta el elemento.
- No commitear, no ejecutar tests, no ejecutar graphify.

## Referencia visual

Mockup aprobado de la dirección Atelier (dashboard): artifact "Financial OS — Propuesta de rediseño UX/UI", sección "C · Atelier" (https://claude.ai/code/artifact/a5f759ec-d1d9-484a-8a05-4f13feeafc79). Rasgos clave: lienzo #F2F3F5, sidebar translúcido, hero grafito con cifra 40px y sparkline verde menta, 3 KPI blancas con sombra suave, fila de insight con ✦ y CTA "Ver desglose →".
