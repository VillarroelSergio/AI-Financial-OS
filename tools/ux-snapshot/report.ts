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
