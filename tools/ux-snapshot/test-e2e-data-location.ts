import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const toolDir = path.dirname(fileURLToPath(import.meta.url));
const source = await readFile(path.join(toolDir, "run-flow-01-05.ts"), "utf8");

assert.match(source, /from "node:os"/);
assert.match(source, /tmpdir\(\)/);
assert.doesNotMatch(source, /path\.join\(PROJECT_ROOT, "\.e2e-data"/);

console.log("E2E temporary data is kept outside the repository.");
