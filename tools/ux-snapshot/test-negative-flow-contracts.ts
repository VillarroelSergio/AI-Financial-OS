import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { loadNegativeFlowContracts, validateNegativeFlowContracts } from "./flow-contracts.js";

const toolDir = path.dirname(fileURLToPath(import.meta.url));
const catalogPath = path.resolve(toolDir, "../../vault/docs/testing/flows/negative-cases.yaml");

const catalog = await loadNegativeFlowContracts(catalogPath);
const errors = validateNegativeFlowContracts(catalog);

assert.deepEqual(errors, [], errors.join("\n"));
assert.equal(catalog.negative_cases.length, 15);
assert.deepEqual(catalog.negative_cases.map((entry) => entry.id), Array.from({ length: 15 }, (_, index) => `NEG-${String(index + 1).padStart(2, "0")}`));
assert.ok(catalog.negative_cases.every((entry) => entry.priority === "required" || entry.priority === "important"));

console.log(`Validated ${catalog.negative_cases.length} negative flow contracts.`);
