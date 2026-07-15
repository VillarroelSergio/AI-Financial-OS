import { chromium } from "playwright";
import { spawn, execSync, type ChildProcess } from "child_process";
import { mkdir, writeFile, readFile } from "fs/promises";
import path from "path";
import { fileURLToPath } from "url";
import { snapshotRoutes } from "./snapshot-routes.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(__dirname, "../..");
const DESKTOP_DIR = path.join(PROJECT_ROOT, "apps", "desktop");
// Mock usa 1422; real usa 1420 porque es el único origen que el backend tiene en
// su whitelist CORS (app.main.py). Con 1422 el navegador bloquearía los fetch.
const REAL = process.argv.includes("--real");
const SNAPSHOT_PORT = REAL ? 1420 : 1422;
const BASE_URL = `http://localhost:${SNAPSHOT_PORT}`;
const BACKEND_URL = process.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8010";

const VIEWPORTS = {
  desktop: { width: 1440, height: 900 },
  tablet: { width: 820, height: 1180 },
  mobile: { width: 390, height: 844 },
} as const;
type ViewportName = keyof typeof VIEWPORTS;

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

async function startVite(useMock: boolean): Promise<ChildProcess> {
  const isWin = process.platform === "win32";
  const [viteCmd, viteArgs] = isWin
    ? (["cmd.exe", ["/c", "npx.cmd", "vite", "--port", String(SNAPSHOT_PORT), "--strictPort"]] as const)
    : (["npx", ["vite", "--port", String(SNAPSHOT_PORT), "--strictPort"]] as const);

  // En modo real NO seteamos VITE_USE_MOCK_DATA → el frontend hace fetch al backend en 8010.
  const env = useMock
    ? { ...process.env, VITE_USE_MOCK_DATA: "true" }
    : { ...process.env, VITE_USE_MOCK_DATA: "false", VITE_API_BASE_URL: BACKEND_URL };
  const proc = spawn(viteCmd, [...viteArgs], {
    cwd: DESKTOP_DIR,
    env,
    stdio: "pipe",
  });

  proc.stderr?.on("data", (d: Buffer) => {
    const msg = d.toString();
    if (msg.includes("error") || msg.includes("Error")) process.stderr.write(msg);
  });

  await new Promise((resolve) => setTimeout(resolve, 300));
  if (proc.exitCode !== null) {
    throw new Error(`Vite no pudo iniciarse en el puerto ${SNAPSHOT_PORT}`);
  }
  await waitForServer(BASE_URL);
  return proc;
}

interface ScreenshotMeta {
  filename: string;
  route: string;
  screen_name: string;
  state: string;
  description: string;
  viewport: ViewportName;
  viewport_size: { width: number; height: number };
  captured: boolean;
  skip_reason?: string;
}

function generateMarkdown(screenshots: ScreenshotMeta[], generatedAt: string, useMock: boolean): string {
  const captured = screenshots.filter((s) => s.captured);
  const skipped = screenshots.filter((s) => !s.captured);
  const viewportLabel = Array.from(
    new Set(screenshots.map((s) => `${s.viewport} ${s.viewport_size.width}x${s.viewport_size.height}`)),
  ).join(", ");

  const rows = captured
    .map((s) => `| \`${s.filename}\` | ${s.screen_name} | ${s.viewport} | ${s.state} | ${s.description} |`)
    .join("\n");

  const skipRows = skipped
    .map((s) => `- **${s.filename}**: ${s.skip_reason ?? "skipped"}`)
    .join("\n");

  return `# UX Review Context - AI Financial OS

> Generated: ${generatedAt}
> Viewports: ${viewportLabel}
> Data: ${useMock ? "mock (no datos reales de usuario)" : "REAL (backend en 8010, datos de usuario)"}

## Como usar estas capturas

Estas capturas representan el estado visual actual de cada pantalla principal.
Usalas para revisar el diseno, detectar regresiones visuales o dar contexto a agentes de IA
sin necesidad de arrancar la app ni tener datos reales.

Para regenerar desktop: \`npm run snapshots\` desde \`tools/ux-snapshot/\`.
Para regenerar desktop/tablet/mobile: \`npm run snapshots:responsive\`.

## Pantallas capturadas

| Archivo | Pantalla | Viewport | Estado | Descripcion |
|---------|----------|----------|--------|-------------|
${rows}

${skipped.length > 0 ? `## Capturas omitidas (requieren interaccion manual)\n\n${skipRows}\n` : ""}
## Notas para agentes

- Las metricas mostradas son ficticias (mock data) y sirven solo para verificar el layout.
- Las pruebas responsive generan variantes desktop, tablet y mobile con el mismo contrato de rutas.
`;
}

async function stopVite(viteProc: ChildProcess): Promise<void> {
  const isWin = process.platform === "win32";
  if (isWin && viteProc.pid != null) {
    try {
      execSync(`taskkill /F /T /PID ${viteProc.pid}`, { stdio: "ignore" });
    } catch {
      viteProc.kill();
    }
    try {
      const netstat = execSync("netstat -ano", { encoding: "utf8" });
      const listener = netstat
        .split(/\r?\n/)
        .find((line) => line.includes(`:${SNAPSHOT_PORT}`) && line.includes("LISTENING"));
      const listenerPid = listener?.trim().split(/\s+/).at(-1);
      if (listenerPid && listenerPid !== "0") {
        execSync(`taskkill /F /T /PID ${listenerPid}`, { stdio: "ignore" });
      }
    } catch {
      // The listener already stopped.
    }
  } else {
    viteProc.kill();
  }

  if (viteProc.exitCode === null) {
    await Promise.race([
      new Promise<void>((r) => viteProc.once("close", () => r())),
      new Promise<void>((r) => setTimeout(r, 2_000)),
    ]);
  }
}

async function main(): Promise<void> {
  const headed = process.argv.includes("--headed");
  const real = REAL;
  const useMock = !real;
  const OUTPUT_DIR = path.join(PROJECT_ROOT, "ux-snapshots", real ? "real" : "latest");
  const responsive = process.argv.includes("--responsive");

  if (real) {
    try {
      const res = await fetch(`${BACKEND_URL}/health`);
      if (!res.ok) throw new Error(`status ${res.status}`);
      console.log(`Backend real OK en ${BACKEND_URL}`);
    } catch (e) {
      throw new Error(
        `Modo --real: el backend no responde en ${BACKEND_URL}/health (${String(e)}). ` +
          `Arráncalo antes: cd backend && python run_server.py`,
      );
    }
  }
  const viewportArg = process.argv.find((a) => a.startsWith("--viewport="));
  const viewportName = (viewportArg?.split("=")[1] ?? "desktop") as ViewportName;
  const filterArg = process.argv.find((a) => a.startsWith("--filter="));
  const filterPath = filterArg ? filterArg.split("=")[1] : null;
  const selectedViewports = responsive ? (Object.keys(VIEWPORTS) as ViewportName[]) : [viewportName];

  for (const name of selectedViewports) {
    if (!VIEWPORTS[name]) throw new Error(`Viewport no soportado: ${name}`);
  }

  const pkgRaw = await readFile(path.join(PROJECT_ROOT, "apps", "desktop", "package.json"), "utf-8");
  const pkg = JSON.parse(pkgRaw) as { version: string };

  await mkdir(OUTPUT_DIR, { recursive: true });

  console.log(useMock ? "Arrancando Vite con mock data..." : "Arrancando Vite contra backend real...");
  const viteProc = await startVite(useMock);
  console.log(`Vite listo en ${BASE_URL}`);

  const browser = await chromium.launch({ headless: !headed });
  const context = await browser.newContext({ viewport: VIEWPORTS[selectedViewports[0]] });
  const page = await context.newPage();

  const screenshots: ScreenshotMeta[] = [];
  const generatedAt = new Date().toISOString();
  const activeRoutes = filterPath
    ? snapshotRoutes.filter((r) => r.path.startsWith(filterPath))
    : snapshotRoutes;

  if (filterPath) {
    console.log(`Filtrando rutas: ${filterPath} (${activeRoutes.length} rutas)`);
  }

  try {
    for (const viewport of selectedViewports) {
      await page.setViewportSize(VIEWPORTS[viewport]);
      for (const route of activeRoutes) {
        const filename = responsive ? route.filename.replace(/\.png$/, `-${viewport}.png`) : route.filename;

        if (route.requiresInteraction) {
          console.log(`Omitiendo ${filename} (requiere interaccion manual)`);
          screenshots.push({
            filename,
            route: route.path,
            screen_name: route.screenName,
            state: route.state,
            description: route.description,
            viewport,
            viewport_size: VIEWPORTS[viewport],
            captured: false,
            skip_reason: "requires manual file upload interaction",
          });
          continue;
        }

        console.log(`Capturando ${filename}...`);
        await page.goto(`${BASE_URL}${route.path}`, { waitUntil: "networkidle" });
        await page.waitForSelector('[data-app-ready="true"]', { timeout: 10_000 });
        await page.waitForTimeout(600);

        const outPath = path.join(OUTPUT_DIR, filename);
        await page.screenshot({ path: outPath, fullPage: false });

        screenshots.push({
          filename,
          route: route.path,
          screen_name: route.screenName,
          state: route.state,
          description: route.description,
          viewport,
          viewport_size: VIEWPORTS[viewport],
          captured: true,
        });
        console.log(`Guardado: ${outPath}`);
      }
    }
  } finally {
    await browser.close();
    await stopVite(viteProc);
    console.log("Navegador y Vite cerrados");
  }

  const metadata = {
    generatedAt,
    appVersion: pkg.version,
    viewport: VIEWPORTS[selectedViewports[0]],
    viewports: selectedViewports.map((name) => ({ name, ...VIEWPORTS[name] })),
    base_url: BASE_URL,
    mock_data: useMock,
    backend_url: real ? BACKEND_URL : null,
    screenshots,
  };

  await writeFile(path.join(OUTPUT_DIR, "metadata.json"), JSON.stringify(metadata, null, 2) + "\n");
  await writeFile(path.join(OUTPUT_DIR, "UX_REVIEW_CONTEXT.md"), generateMarkdown(screenshots, generatedAt, useMock));

  const capturedCount = screenshots.filter((s) => s.captured).length;
  console.log(`\n${capturedCount}/${activeRoutes.length * selectedViewports.length} capturas generadas en ${OUTPUT_DIR}`);
}

main().catch((err) => {
  console.error("Error:", err);
  process.exit(1);
});
