# UX Snapshot Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Crear una herramienta interna (`tools/ux-snapshot`) que genere capturas automáticas de las pantallas principales de AI Financial OS usando Playwright con mock data, sin necesitar datos reales del usuario.

**Architecture:** La herramienta vive en `tools/ux-snapshot/` (paquete Node autocontenido con Playwright) y se integra con `apps/desktop` mediante scripts npm. La app React detecta `VITE_USE_MOCK_DATA=true` y devuelve fixtures locales en vez de llamar al backend. Playwright arranca Vite en puerto 1422 (diferente al de desarrollo, 1420), navega a cada ruta, espera `[data-app-ready="true"]` y captura. El output va a `ux-snapshots/latest/`.

**Tech Stack:** Playwright 1.49, tsx 4.19, TypeScript 5.6, Vite 6, React 18, react-router-dom 6.

## Global Constraints

- Windows-first: comandos y paths deben funcionar en PowerShell / npm scripts en Windows.
- No modificar estilos visuales ni lógica de negocio.
- No añadir dependencias de producción; solo devDependencies.
- Viewport estándar: 1440×900.
- Puerto snapshot: 1422 (no 1420 para no colisionar con dev).
- Output siempre en `ux-snapshots/latest/` relativo a la raíz del proyecto.
- Nombres de archivo estables (no incluir timestamps en los PNGs).
- Código tipado strict, sin `any`.
- UI en español (ya existente); no modificar copy.

---

### Task 1: Mock data layer + `data-app-ready` attribute

**Goal:** La app React puede funcionar sin backend cuando `VITE_USE_MOCK_DATA=true`. El layout raíz expone `data-app-ready="true"` para que Playwright sepa que el DOM está listo.

**Files:**
- Create: `apps/desktop/src/lib/api/mock-data.ts`
- Modify: `apps/desktop/src/lib/api/client.ts`
- Modify: `apps/desktop/src/app/layout/RootLayout.tsx`

**Interfaces:**
- Produces: `getMockResponse<T>(path: string, method: string): T` (consumido por client.ts modificado)
- Produces: `data-app-ready="true"` en el div raíz de RootLayout (consumido por Playwright)

- [ ] **Step 1: Crear `mock-data.ts`**

Crear `apps/desktop/src/lib/api/mock-data.ts` con el contenido completo:

```typescript
import type { Account, Category, Transaction, DashboardOverview } from "@/lib/types";
import type { SpendingData, CategorySpending } from "./dashboard";
import type { AppSetting } from "./settings";

const mockAccounts: Account[] = [
  {
    id: "mock-acc-1",
    name: "BBVA Cuenta Corriente",
    type: "bank",
    institution: "BBVA",
    currency: "EUR",
    current_balance: "12450.00",
    is_active: true,
    created_at: "2024-01-01T00:00:00",
    updated_at: "2024-01-01T00:00:00",
  },
  {
    id: "mock-acc-2",
    name: "Cartera MyInvestor",
    type: "broker",
    institution: "MyInvestor",
    currency: "EUR",
    current_balance: "28900.00",
    is_active: true,
    created_at: "2024-01-01T00:00:00",
    updated_at: "2024-01-01T00:00:00",
  },
  {
    id: "mock-acc-3",
    name: "Efectivo",
    type: "cash",
    institution: null,
    currency: "EUR",
    current_balance: "350.00",
    is_active: true,
    created_at: "2024-01-01T00:00:00",
    updated_at: "2024-01-01T00:00:00",
  },
];

const mockCategories: Category[] = [
  { id: "cat-1", name: "Alimentación", parent_id: null, type: "expense", icon: null, color: "#ec7e00", is_system: true, created_at: "2024-01-01T00:00:00", updated_at: "2024-01-01T00:00:00" },
  { id: "cat-2", name: "Transporte", parent_id: null, type: "expense", icon: null, color: "#494fdf", is_system: true, created_at: "2024-01-01T00:00:00", updated_at: "2024-01-01T00:00:00" },
  { id: "cat-3", name: "Ocio", parent_id: null, type: "expense", icon: null, color: "#00a87e", is_system: true, created_at: "2024-01-01T00:00:00", updated_at: "2024-01-01T00:00:00" },
  { id: "cat-4", name: "Casa", parent_id: null, type: "expense", icon: null, color: "#e23b4a", is_system: true, created_at: "2024-01-01T00:00:00", updated_at: "2024-01-01T00:00:00" },
  { id: "cat-5", name: "Salario", parent_id: null, type: "income", icon: null, color: "#4f55f1", is_system: true, created_at: "2024-01-01T00:00:00", updated_at: "2024-01-01T00:00:00" },
];

const mockTransactions: Transaction[] = [
  { id: "tx-1", account_id: "mock-acc-1", category_id: "cat-1", date: "2026-06-20", description: "Mercadona", amount: "-87.40", currency: "EUR", converted_amount: null, converted_currency: null, type: "expense", source: "manual", source_name: null, external_id: null, import_batch_id: null, notes: null, created_at: "2026-06-20T10:00:00", updated_at: "2026-06-20T10:00:00" },
  { id: "tx-2", account_id: "mock-acc-1", category_id: "cat-2", date: "2026-06-19", description: "Renfe AVE Madrid", amount: "-42.50", currency: "EUR", converted_amount: null, converted_currency: null, type: "expense", source: "manual", source_name: null, external_id: null, import_batch_id: null, notes: null, created_at: "2026-06-19T10:00:00", updated_at: "2026-06-19T10:00:00" },
  { id: "tx-3", account_id: "mock-acc-1", category_id: "cat-3", date: "2026-06-18", description: "Netflix", amount: "-15.99", currency: "EUR", converted_amount: null, converted_currency: null, type: "expense", source: "manual", source_name: null, external_id: null, import_batch_id: null, notes: null, created_at: "2026-06-18T10:00:00", updated_at: "2026-06-18T10:00:00" },
  { id: "tx-4", account_id: "mock-acc-1", category_id: "cat-4", date: "2026-06-15", description: "Alquiler junio", amount: "-950.00", currency: "EUR", converted_amount: null, converted_currency: null, type: "expense", source: "manual", source_name: null, external_id: null, import_batch_id: null, notes: null, created_at: "2026-06-15T10:00:00", updated_at: "2026-06-15T10:00:00" },
  { id: "tx-5", account_id: "mock-acc-1", category_id: "cat-5", date: "2026-06-01", description: "Nómina junio", amount: "2800.00", currency: "EUR", converted_amount: null, converted_currency: null, type: "income", source: "manual", source_name: null, external_id: null, import_batch_id: null, notes: null, created_at: "2026-06-01T10:00:00", updated_at: "2026-06-01T10:00:00" },
];

const mockOverview: DashboardOverview = {
  net_worth: "41700.00",
  liquidity: "12800.00",
  investments: "28900.00",
  monthly_income: "2800.00",
  monthly_expense: "1095.89",
  monthly_savings: "1704.11",
  savings_rate: 0.608,
  currency: "EUR",
};

const mockSpendingCategories: CategorySpending[] = [
  { category_id: "cat-4", category: "Casa", amount: "950.00", percentage: 86.7 },
  { category_id: "cat-1", category: "Alimentación", amount: "87.40", percentage: 8.0 },
  { category_id: "cat-2", category: "Transporte", amount: "42.50", percentage: 3.9 },
  { category_id: "cat-3", category: "Ocio", amount: "15.99", percentage: 1.4 },
];

const mockSpending: SpendingData = {
  month: "2026-06",
  total_expense: "1095.89",
  total_income: "2800.00",
  by_category: mockSpendingCategories,
};

const mockSettings: AppSetting[] = [
  { id: "set-1", key: "app.language", value_json: '"es"', created_at: "2024-01-01T00:00:00", updated_at: "2024-01-01T00:00:00" },
  { id: "set-2", key: "theme.mode", value_json: '"dark"', created_at: "2024-01-01T00:00:00", updated_at: "2024-01-01T00:00:00" },
  { id: "set-3", key: "app.currency", value_json: '"EUR"', created_at: "2024-01-01T00:00:00", updated_at: "2024-01-01T00:00:00" },
];

export function getMockResponse<T>(path: string): T {
  const clean = path.split("?")[0];

  if (clean === "/api/accounts") return mockAccounts as T;
  if (clean === "/api/categories") return mockCategories as T;
  if (clean === "/api/transactions") return mockTransactions as T;
  if (clean === "/api/dashboard/overview") return mockOverview as T;
  if (clean === "/api/dashboard/spending") return mockSpending as T;
  if (clean === "/api/settings") return mockSettings as T;

  throw new Error(`[mock] No mock defined for: ${path}`);
}
```

- [ ] **Step 2: Modificar `client.ts` para usar mock data**

Leer `apps/desktop/src/lib/api/client.ts` y reemplazar por:

```typescript
import { getMockResponse } from "./mock-data";

const BASE_URL = "http://127.0.0.1:8000";
const USE_MOCK = import.meta.env.VITE_USE_MOCK_DATA === "true";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  if (USE_MOCK) {
    return Promise.resolve(getMockResponse<T>(path));
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });

  if (!response.ok) {
    const body = await response
      .json()
      .catch(() => ({ error: { code: "UNKNOWN", message: response.statusText } }));
    throw new ApiError(
      response.status,
      body.error?.code ?? "UNKNOWN",
      body.error?.message ?? response.statusText,
    );
  }

  return response.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};
```

- [ ] **Step 3: Añadir `data-app-ready` a RootLayout**

En `apps/desktop/src/app/layout/RootLayout.tsx`, añadir `data-app-ready="true"` al div raíz:

```tsx
// Línea 40: cambiar
<div className="flex h-full">
// Por:
<div className="flex h-full" data-app-ready="true">
```

- [ ] **Step 4: Verificar TypeScript**

```powershell
cd apps/desktop
npx tsc --noEmit
```

Expected: sin errores.

- [ ] **Step 5: Verificar mock data en browser**

Arrancar Vite con mock:
```powershell
$env:VITE_USE_MOCK_DATA="true"; npm run dev -- --port 1422
```
Abrir `http://localhost:1422/` — debe mostrar datos de overview (Patrimonio €41.700, Liquidez €12.800, Inversiones €28.900). Abrir `/spending` — debe mostrar pie chart con categorías. Cerrar el servidor.

---

### Task 2: Herramienta Playwright (`tools/ux-snapshot`)

**Goal:** Paquete Node autocontenido que abre un navegador headless, navega cada ruta y guarda PNG + metadata.

**Files:**
- Create: `tools/ux-snapshot/package.json`
- Create: `tools/ux-snapshot/tsconfig.json`
- Create: `tools/ux-snapshot/snapshot-routes.ts`
- Create: `tools/ux-snapshot/run-ux-snapshots.ts`
- Create: `tools/ux-snapshot/report.ts`

**Interfaces:**
- Consumes: `data-app-ready="true"` en el DOM (de Task 1)
- Consumes: Vite dev server en `http://localhost:1422` con `VITE_USE_MOCK_DATA=true`
- Produces: `ux-snapshots/latest/*.png`, `ux-snapshots/latest/metadata.json`, `ux-snapshots/latest/UX_REVIEW_CONTEXT.md`

- [ ] **Step 1: Crear `tools/ux-snapshot/package.json`**

```json
{
  "name": "ux-snapshot",
  "version": "1.0.0",
  "description": "UX snapshot tool for AI Financial OS — generates Playwright screenshots with mock data",
  "type": "module",
  "scripts": {
    "snapshots": "tsx run-ux-snapshots.ts",
    "snapshots:headed": "tsx run-ux-snapshots.ts --headed",
    "report": "tsx report.ts"
  },
  "devDependencies": {
    "playwright": "^1.49.0",
    "tsx": "^4.19.0",
    "@types/node": "^22.0.0"
  }
}
```

- [ ] **Step 2: Crear `tools/ux-snapshot/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "outDir": "dist"
  },
  "include": ["*.ts"]
}
```

- [ ] **Step 3: Crear `tools/ux-snapshot/snapshot-routes.ts`**

```typescript
export interface SnapshotRoute {
  path: string;
  filename: string;
  screenName: string;
  state: string;
  description: string;
  requiresInteraction: boolean;
}

export const snapshotRoutes: SnapshotRoute[] = [
  {
    path: "/",
    filename: "overview.png",
    screenName: "Overview",
    state: "mock_data",
    description: "Dashboard principal con patrimonio neto, liquidez, inversiones y métricas del mes",
    requiresInteraction: false,
  },
  {
    path: "/spending",
    filename: "spending.png",
    screenName: "Spending",
    state: "mock_data",
    description: "Análisis de gastos mensual con pie chart por categoría y desglose",
    requiresInteraction: false,
  },
  {
    path: "/investments",
    filename: "investments.png",
    screenName: "Investments",
    state: "empty",
    description: "Cartera de inversiones — estado inicial sin datos",
    requiresInteraction: false,
  },
  {
    path: "/goals",
    filename: "goals.png",
    screenName: "Goals",
    state: "empty",
    description: "Objetivos financieros — estado inicial sin objetivos",
    requiresInteraction: false,
  },
  {
    path: "/economy",
    filename: "economy.png",
    screenName: "Economy",
    state: "empty",
    description: "Indicadores macroeconómicos — estado inicial",
    requiresInteraction: false,
  },
  {
    path: "/insights",
    filename: "insights.png",
    screenName: "Insights",
    state: "empty",
    description: "Insights personalizados — estado inicial sin análisis",
    requiresInteraction: false,
  },
  {
    path: "/imports",
    filename: "imports-empty.png",
    screenName: "Imports (empty)",
    state: "empty",
    description: "Centro de importación — estado vacío antes de seleccionar archivo",
    requiresInteraction: false,
  },
  {
    path: "/imports",
    filename: "imports-preview.png",
    screenName: "Imports (preview)",
    state: "empty",
    description: "Centro de importación — estado vacío (preview requiere interacción manual con archivo CSV real)",
    requiresInteraction: true,
  },
  {
    path: "/settings",
    filename: "settings.png",
    screenName: "Settings",
    state: "mock_data",
    description: "Configuración de la aplicación — idioma, moneda y tema",
    requiresInteraction: false,
  },
];
```

- [ ] **Step 4: Crear `tools/ux-snapshot/run-ux-snapshots.ts`**

```typescript
import { chromium } from "playwright";
import { spawn, type ChildProcess } from "child_process";
import { mkdir, writeFile } from "fs/promises";
import { existsSync } from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { snapshotRoutes, type SnapshotRoute } from "./snapshot-routes.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(__dirname, "../..");
const DESKTOP_DIR = path.join(PROJECT_ROOT, "apps", "desktop");
const OUTPUT_DIR = path.join(PROJECT_ROOT, "ux-snapshots", "latest");
const SNAPSHOT_PORT = 1422;
const BASE_URL = `http://localhost:${SNAPSHOT_PORT}`;
const VIEWPORT = { width: 1440, height: 900 };

async function waitForServer(url: string, timeoutMs = 30_000): Promise<void> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const res = await fetch(url);
      if (res.status < 500) return;
    } catch {
      // not ready yet
    }
    await new Promise((r) => setTimeout(r, 500));
  }
  throw new Error(`Server at ${url} did not respond within ${timeoutMs}ms`);
}

async function startVite(): Promise<ChildProcess> {
  const viteCmd = process.platform === "win32" ? "npx.cmd" : "npx";
  const proc = spawn(viteCmd, ["vite", "--port", String(SNAPSHOT_PORT), "--strictPort"], {
    cwd: DESKTOP_DIR,
    env: { ...process.env, VITE_USE_MOCK_DATA: "true" },
    stdio: "pipe",
  });

  proc.stderr?.on("data", (d: Buffer) => {
    const msg = d.toString();
    if (msg.includes("error") || msg.includes("Error")) process.stderr.write(msg);
  });

  await waitForServer(BASE_URL);
  return proc;
}

interface ScreenshotMeta {
  filename: string;
  route: string;
  screen_name: string;
  state: string;
  description: string;
  captured: boolean;
  skip_reason?: string;
}

function generateMarkdown(
  screenshots: ScreenshotMeta[],
  generatedAt: string,
): string {
  const captured = screenshots.filter((s) => s.captured);
  const skipped = screenshots.filter((s) => !s.captured);

  const rows = captured
    .map(
      (s) =>
        `| \`${s.filename}\` | ${s.screen_name} | ${s.state} | ${s.description} |`,
    )
    .join("\n");

  const skipRows = skipped
    .map((s) => `- **${s.filename}**: ${s.skip_reason ?? "skipped"}`)
    .join("\n");

  return `# UX Review Context — AI Financial OS

> Generated: ${generatedAt}  
> Viewport: ${VIEWPORT.width}×${VIEWPORT.height}  
> Data: mock (no datos reales de usuario)

## Cómo usar estas capturas

Estas capturas representan el estado visual actual de cada pantalla principal.
Úsalas para revisar el diseño, detectar regresiones visuales o dar contexto a agentes de IA
sin necesidad de arrancar la app ni tener datos reales.

Para regenerar: \`npm run ux:snapshots\` desde \`apps/desktop/\`.

## Pantallas capturadas

| Archivo | Pantalla | Estado | Descripción |
|---------|----------|--------|-------------|
${rows}

${skipped.length > 0 ? `## Capturas omitidas (requieren interacción manual)\n\n${skipRows}\n` : ""}
## Notas para agentes

- Las pantallas \`investments\`, \`goals\`, \`economy\` e \`insights\` muestran estados vacíos
  porque aún no tienen implementación de datos en las fases actuales del roadmap.
- \`imports-preview.png\` requiere que el usuario suba un archivo CSV real; omitida en modo automático.
- Las métricas mostradas son ficticias (mock data) y sirven solo para verificar el layout.
`;
}

async function main(): Promise<void> {
  const headed = process.argv.includes("--headed");

  await mkdir(OUTPUT_DIR, { recursive: true });

  console.log("▶  Arrancando Vite con mock data…");
  const viteProc = await startVite();
  console.log(`✓  Vite listo en ${BASE_URL}`);

  const browser = await chromium.launch({ headless: !headed });
  const context = await browser.newContext({ viewport: VIEWPORT });
  const page = await context.newPage();

  const screenshots: ScreenshotMeta[] = [];
  const generatedAt = new Date().toISOString();

  try {
    for (const route of snapshotRoutes) {
      if (route.requiresInteraction) {
        console.log(`⊘  Omitiendo ${route.filename} (requiere interacción manual)`);
        screenshots.push({
          filename: route.filename,
          route: route.path,
          screen_name: route.screenName,
          state: route.state,
          description: route.description,
          captured: false,
          skip_reason: "requires manual file upload interaction",
        });
        continue;
      }

      console.log(`📸 Capturando ${route.filename}…`);
      await page.goto(`${BASE_URL}${route.path}`, { waitUntil: "networkidle" });
      await page.waitForSelector('[data-app-ready="true"]', { timeout: 10_000 });
      await page.waitForTimeout(600); // let React finish rendering async state

      const outPath = path.join(OUTPUT_DIR, route.filename);
      await page.screenshot({ path: outPath, fullPage: false });

      screenshots.push({
        filename: route.filename,
        route: route.path,
        screen_name: route.screenName,
        state: route.state,
        description: route.description,
        captured: true,
      });
      console.log(`✓  Guardado: ${outPath}`);
    }
  } finally {
    await browser.close();
    viteProc.kill();
    console.log("✓  Navegador y Vite cerrados");
  }

  const metadata = {
    generated_at: generatedAt,
    viewport: VIEWPORT,
    base_url: BASE_URL,
    mock_data: true,
    screenshots,
  };

  await writeFile(
    path.join(OUTPUT_DIR, "metadata.json"),
    JSON.stringify(metadata, null, 2),
  );

  await writeFile(
    path.join(OUTPUT_DIR, "UX_REVIEW_CONTEXT.md"),
    generateMarkdown(screenshots, generatedAt),
  );

  const capturedCount = screenshots.filter((s) => s.captured).length;
  console.log(`\n✅ ${capturedCount}/${snapshotRoutes.length} capturas generadas en ${OUTPUT_DIR}`);
}

main().catch((err) => {
  console.error("❌ Error:", err);
  process.exit(1);
});
```

- [ ] **Step 5: Crear `tools/ux-snapshot/report.ts`**

```typescript
import { readFile } from "fs/promises";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(__dirname, "../..");
const METADATA_PATH = path.join(PROJECT_ROOT, "ux-snapshots", "latest", "metadata.json");

interface ScreenshotMeta {
  filename: string;
  route: string;
  screen_name: string;
  state: string;
  captured: boolean;
}

interface Metadata {
  generated_at: string;
  viewport: { width: number; height: number };
  screenshots: ScreenshotMeta[];
}

async function main(): Promise<void> {
  let raw: string;
  try {
    raw = await readFile(METADATA_PATH, "utf-8");
  } catch {
    console.error("❌ No se encontró metadata.json. Ejecuta primero: npm run ux:snapshots");
    process.exit(1);
  }

  const meta: Metadata = JSON.parse(raw) as Metadata;
  const captured = meta.screenshots.filter((s) => s.captured);
  const skipped = meta.screenshots.filter((s) => !s.captured);

  console.log("\n📊 UX Snapshot Report — AI Financial OS");
  console.log("─".repeat(50));
  console.log(`Generado: ${meta.generated_at}`);
  console.log(`Viewport: ${meta.viewport.width}×${meta.viewport.height}`);
  console.log(`Capturas: ${captured.length} ok / ${skipped.length} omitidas\n`);

  console.log("Capturas generadas:");
  for (const s of captured) {
    console.log(`  ✓ ${s.filename.padEnd(24)} ${s.route}`);
  }

  if (skipped.length > 0) {
    console.log("\nOmitidas:");
    for (const s of skipped) {
      console.log(`  ⊘ ${s.filename.padEnd(24)} (interacción manual requerida)`);
    }
  }

  console.log(`\nDirectorio: ux-snapshots/latest/`);
}

main().catch(console.error);
```

- [ ] **Step 6: Instalar dependencias del tool**

```powershell
cd tools/ux-snapshot
npm install
npx playwright install chromium
```

Expected: `node_modules/playwright` instalado, Chromium descargado.

- [ ] **Step 7: Verificar que el tool funciona aislado**

```powershell
# Desde tools/ux-snapshot (con Vite ya arrancado en puerto 1422 con mock)
npm run snapshots
```

Expected: carpeta `ux-snapshots/latest/` creada con PNGs y metadata.json.

---

### Task 3: Scripts npm + `.gitignore` + actualización de docs

**Goal:** Los scripts `ux:snapshots`, `ux:snapshots:headed` y `ux:report` están disponibles en `apps/desktop`. Los PNGs se excluyen del repo (son artefactos generados). Los docs guían a futuros agentes.

**Files:**
- Modify: `apps/desktop/package.json`
- Create: `ux-snapshots/.gitignore`
- Modify: `docs/08_UX_UI_GUIDELINES.md`
- Modify: `docs/13_CLAUDE_CODE_GUIDE.md`

**Interfaces:**
- Consumes: `tools/ux-snapshot/package.json` scripts (de Task 2)
- Produces: `npm run ux:snapshots` ejecutable desde `apps/desktop`

- [ ] **Step 1: Actualizar `apps/desktop/package.json`**

Añadir los scripts `ux:*` al bloque `"scripts"`:

```json
{
  "name": "ai-financial-os-desktop",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "tauri": "tauri",
    "ux:snapshots": "npm install --prefix ../../tools/ux-snapshot && npm run snapshots --prefix ../../tools/ux-snapshot",
    "ux:snapshots:headed": "npm install --prefix ../../tools/ux-snapshot && npm run snapshots:headed --prefix ../../tools/ux-snapshot",
    "ux:report": "npm run report --prefix ../../tools/ux-snapshot"
  },
  "dependencies": { ... },
  "devDependencies": { ... }
}
```

(Mantener `dependencies` y `devDependencies` existentes intactas.)

- [ ] **Step 2: Crear `.gitignore` para ux-snapshots**

Crear `ux-snapshots/.gitignore`:

```gitignore
# Generated screenshots — do not commit
*.png

# Keep structure and context files
!.gitignore
```

- [ ] **Step 3: Añadir sección de UX Snapshots en `docs/13_CLAUDE_CODE_GUIDE.md`**

Añadir al final del archivo:

```markdown

---

## Herramienta UX Snapshots

### Descripción

`tools/ux-snapshot` genera capturas automáticas de las pantallas principales usando Playwright con mock data. Sirve para que Claude Code y otros agentes tengan contexto visual actualizado sin necesitar datos reales del usuario ni tener la app arrancada manualmente.

### Comandos

Desde `apps/desktop/`:

```bash
# Capturar todas las pantallas (headless)
npm run ux:snapshots

# Capturar con navegador visible (debug)
npm run ux:snapshots:headed

# Ver resumen del último run
npm run ux:report
```

### Output

- `ux-snapshots/latest/*.png` — Capturas estables por pantalla (1440×900)
- `ux-snapshots/latest/metadata.json` — Fecha, viewport, ruta y estado de cada captura
- `ux-snapshots/latest/UX_REVIEW_CONTEXT.md` — Contexto completo para revisión

### Cómo funciona

1. Arranca Vite en el puerto 1422 con `VITE_USE_MOCK_DATA=true`.
2. La app React usa fixtures locales en vez de llamar al backend.
3. Playwright navega a cada ruta y espera `[data-app-ready="true"]` en el DOM.
4. Captura y guarda PNG con nombre estable.
5. Genera metadata.json y UX_REVIEW_CONTEXT.md.

### Añadir una nueva pantalla

Editar `tools/ux-snapshot/snapshot-routes.ts` y añadir una entrada al array `snapshotRoutes`. Ver la sección correspondiente en `08_UX_UI_GUIDELINES.md`.

### Datos mock

Los fixtures están en `apps/desktop/src/lib/api/mock-data.ts`. Si añades un endpoint nuevo, añade su mock en `getMockResponse()`.
```

- [ ] **Step 4: Añadir regla en `docs/08_UX_UI_GUIDELINES.md`**

Añadir al final del archivo:

```markdown

---

## UX Snapshots

Toda nueva pantalla principal debe registrarse en `tools/ux-snapshot/snapshot-routes.ts` añadiendo una entrada al array `snapshotRoutes` con:

- `path`: ruta de React Router (e.g. `"/markets"`)
- `filename`: nombre estable del PNG (e.g. `"markets.png"`)
- `screenName`: nombre legible (e.g. `"Markets"`)
- `state`: `"mock_data"` si tiene datos, `"empty"` si es estado vacío
- `description`: una línea describiendo qué muestra la pantalla
- `requiresInteraction`: `true` solo si la captura requiere acción del usuario

Si la pantalla consume datos del backend, también añadir los fixtures correspondientes en `apps/desktop/src/lib/api/mock-data.ts`.
```

- [ ] **Step 5: Verificación final end-to-end**

Desde `apps/desktop/`:
```powershell
npm run ux:snapshots
```

Expected output:
```
▶  Arrancando Vite con mock data…
✓  Vite listo en http://localhost:1422
📸 Capturando overview.png…
✓  Guardado: .../ux-snapshots/latest/overview.png
...
✅ 8/9 capturas generadas en .../ux-snapshots/latest
```

Verificar que existen:
- `ux-snapshots/latest/overview.png`
- `ux-snapshots/latest/spending.png`
- `ux-snapshots/latest/investments.png`
- `ux-snapshots/latest/goals.png`
- `ux-snapshots/latest/economy.png`
- `ux-snapshots/latest/insights.png`
- `ux-snapshots/latest/imports-empty.png`
- `ux-snapshots/latest/settings.png`
- `ux-snapshots/latest/metadata.json`
- `ux-snapshots/latest/UX_REVIEW_CONTEXT.md`

```powershell
npm run ux:report
```

Expected: resumen en consola con 8 capturas ok y 1 omitida.

---

## Self-Review

**Spec coverage:**
- ✅ Req 1 — Playwright instalado en tools/ux-snapshot
- ✅ Req 2 — Carpeta /tools/ux-snapshot creada
- ✅ Req 3 — snapshot-routes.ts con 8 rutas (/, /spending, /investments, /goals, /economy, /insights, /imports, /settings)
- ✅ Req 4 — run-ux-snapshots.ts
- ✅ Req 5 — Output en /ux-snapshots/latest
- ✅ Req 6 — Nombres estables (overview.png, spending.png, etc.)
- ✅ Req 7 — metadata.json con fecha, viewport, ruta, nombre, estado, descripción
- ✅ Req 8 — UX_REVIEW_CONTEXT.md dentro de /ux-snapshots/latest
- ✅ Req 9 — Scripts ux:snapshots, ux:snapshots:headed, ux:report en package.json
- ✅ Req 10 — VITE_USE_MOCK_DATA=true en mock-data.ts + client.ts
- ✅ Req 11 — data-app-ready="true" en RootLayout
- ✅ Req 12 — 13_CLAUDE_CODE_GUIDE.md actualizado
- ✅ Req 13 — 08_UX_UI_GUIDELINES.md actualizado
- ✅ Req 14 — Sin cambios visuales
- ✅ Req 15 — Sin cambios de arquitectura salvo los necesarios
- ✅ Req 16 — Código tipado strict

**Placeholder scan:** Ningún TBD, TODO ni paso sin código.

**Type consistency:**
- `SnapshotRoute` definido en snapshot-routes.ts, importado en run-ux-snapshots.ts
- `getMockResponse<T>` retorna `T`, consumido en client.ts con el tipo genérico correcto
- `ScreenshotMeta` definido localmente en run-ux-snapshots.ts y report.ts (sin dependencia cruzada)
