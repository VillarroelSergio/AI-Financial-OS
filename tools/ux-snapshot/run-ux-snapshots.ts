import { chromium } from "playwright";
import { spawn, execSync, type ChildProcess } from "child_process";
import { mkdir, writeFile, readFile } from "fs/promises";
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
  // On Windows, .cmd files must be launched with shell:true or via cmd.exe
  const isWin = process.platform === "win32";
  const [viteCmd, viteArgs] = isWin
    ? (["cmd.exe", ["/c", "npx.cmd", "vite", "--port", String(SNAPSHOT_PORT), "--strictPort"]] as const)
    : (["npx", ["vite", "--port", String(SNAPSHOT_PORT), "--strictPort"]] as const);
  const proc = spawn(viteCmd, [...viteArgs], {
    cwd: DESKTOP_DIR,
    env: { ...process.env, VITE_USE_MOCK_DATA: "true" },
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
  const filterArg = process.argv.find((a) => a.startsWith("--filter="));
  const filterPath = filterArg ? filterArg.split("=")[1] : null;

  // Read app version from desktop package.json
  const pkgRaw = await readFile(
    path.join(PROJECT_ROOT, "apps", "desktop", "package.json"),
    "utf-8",
  );
  const pkg = JSON.parse(pkgRaw) as { version: string };

  await mkdir(OUTPUT_DIR, { recursive: true });

  console.log("▶  Arrancando Vite con mock data…");
  const viteProc = await startVite();
  console.log(`✓  Vite listo en ${BASE_URL}`);

  const browser = await chromium.launch({ headless: !headed });
  const context = await browser.newContext({ viewport: VIEWPORT });
  const page = await context.newPage();

  const screenshots: ScreenshotMeta[] = [];
  const generatedAt = new Date().toISOString();
  const activeRoutes = filterPath
    ? snapshotRoutes.filter((r) => r.path.startsWith(filterPath))
    : snapshotRoutes;

  if (filterPath) {
    console.log(`🔍 Filtrando rutas: ${filterPath} (${activeRoutes.length} capturas)`);
  }

  try {
    for (const route of activeRoutes) {
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
    console.log("✓  Navegador y Vite cerrados");
  }

  // Note: key is `generatedAt` (camelCase), not `generated_at` (snake_case) as in the original plan spec.
  const metadata = {
    generatedAt,
    appVersion: pkg.version,
    viewport: VIEWPORT,
    base_url: BASE_URL,
    mock_data: true,
    screenshots,
  };

  await writeFile(
    path.join(OUTPUT_DIR, "metadata.json"),
    JSON.stringify(metadata, null, 2) + "\n",
  );

  await writeFile(
    path.join(OUTPUT_DIR, "UX_REVIEW_CONTEXT.md"),
    generateMarkdown(screenshots, generatedAt),
  );

  const capturedCount = screenshots.filter((s) => s.captured).length;
  console.log(`\n✅ ${capturedCount}/${activeRoutes.length} capturas generadas en ${OUTPUT_DIR}`);
}

main().catch((err) => {
  console.error("❌ Error:", err);
  process.exit(1);
});
