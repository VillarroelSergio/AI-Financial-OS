import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { loadFlowContracts, validateFlowContracts } from "./flow-contracts.js";

const toolDir = path.dirname(fileURLToPath(import.meta.url));
const catalogPath = path.resolve(toolDir, "../../vault/docs/testing/flows/catalog.yaml");
const fixturePath = path.resolve(toolDir, "../../vault/docs/testing/fixtures/financial-os.yaml");

const catalog = await loadFlowContracts(catalogPath, fixturePath);
const errors = validateFlowContracts(catalog);

assert.deepEqual(errors, [], errors.join("\n"));
assert.equal(catalog.flows.length, 33);
assert.deepEqual(catalog.flows.map((flow) => flow.id), Array.from({ length: 33 }, (_, index) => `FLOW-${String(index + 1).padStart(2, "0")}`));
assert.ok(catalog.flows.every((flow) => flow.steps.length > 0));
assert.ok(catalog.flows.every((flow) => flow.assertions.length > 0));
assert.ok(catalog.flows.filter((flow) => flow.execution === "deterministic").every((flow) => flow.fixture));

console.log(`Validated ${catalog.flows.length} flow contracts.`);
