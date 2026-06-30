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
  viewport?: string;
  captured: boolean;
}

interface Metadata {
  generatedAt: string;
  appVersion: string;
  viewport: { width: number; height: number };
  viewports?: Array<{ name: string; width: number; height: number }>;
  screenshots: ScreenshotMeta[];
}

async function main(): Promise<void> {
  let raw: string;
  try {
    raw = await readFile(METADATA_PATH, "utf-8");
  } catch {
    console.error("No se encontro metadata.json. Ejecuta primero: npm run snapshots");
    process.exit(1);
  }

  const meta: Metadata = JSON.parse(raw) as Metadata;
  const captured = meta.screenshots.filter((s) => s.captured);
  const skipped = meta.screenshots.filter((s) => !s.captured);
  const viewports = meta.viewports?.length
    ? meta.viewports.map((v) => `${v.name} ${v.width}x${v.height}`).join(", ")
    : `${meta.viewport.width}x${meta.viewport.height}`;

  console.log("\nUX Snapshot Report - AI Financial OS");
  console.log("-".repeat(50));
  console.log(`Generado: ${meta.generatedAt}`);
  console.log(`App version: ${meta.appVersion}`);
  console.log(`Viewports: ${viewports}`);
  console.log(`Capturas: ${captured.length} ok / ${skipped.length} omitidas\n`);

  console.log("Capturas generadas:");
  for (const s of captured) {
    const viewport = s.viewport ? `[${s.viewport}]` : "";
    console.log(`  ${s.filename.padEnd(32)} ${viewport.padEnd(10)} ${s.route}`);
  }

  if (skipped.length > 0) {
    console.log("\nOmitidas:");
    for (const s of skipped) {
      console.log(`  ${s.filename.padEnd(32)} (interaccion manual requerida)`);
    }
  }

  console.log("\nDirectorio: ux-snapshots/latest/");
}

main().catch(console.error);
