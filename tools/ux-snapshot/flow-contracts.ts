import { readFile } from "node:fs/promises";
import { parse } from "yaml";

export type FlowStep = { action: string; expected: string };
export type FlowAssertion = { kind: "ui" | "api" | "domain" | "console" | "network"; expected: string };
export type FlowContract = {
  id: string; phase: string; module: string; title: string;
  execution: "deterministic" | "external-smoke"; fixture?: string; route: string;
  preconditions: string[]; steps: FlowStep[]; assertions: FlowAssertion[]; cleanup: string[];
};
export type FlowCatalog = { version: number; flows: FlowContract[]; fixtures: { scenarios: Record<string, unknown> } };

async function readYaml(filePath: string): Promise<unknown> {
  return parse(await readFile(filePath, "utf8"));
}

export async function loadFlowContracts(catalogPath: string, fixturePath: string): Promise<FlowCatalog> {
  const [catalog, fixtures] = await Promise.all([readYaml(catalogPath), readYaml(fixturePath)]);
  return { ...(catalog as Omit<FlowCatalog, "fixtures">), fixtures: fixtures as FlowCatalog["fixtures"] };
}

export function validateFlowContracts(catalog: FlowCatalog): string[] {
  const errors: string[] = [];
  if (catalog.version !== 1) errors.push("catalog.version debe ser 1");
  if (!Array.isArray(catalog.flows)) return [...errors, "catalog.flows debe ser una lista"];
  const ids = new Set<string>();
  for (const flow of catalog.flows) {
    if (!/^FLOW-\d{2}$/.test(flow.id)) errors.push(`${flow.id}: ID inválido`);
    if (ids.has(flow.id)) errors.push(`${flow.id}: ID duplicado`);
    ids.add(flow.id);
    if (!flow.phase || !flow.module || !flow.title || !flow.route) errors.push(`${flow.id}: metadatos incompletos`);
    if (!Array.isArray(flow.preconditions) || flow.preconditions.length === 0) errors.push(`${flow.id}: faltan precondiciones`);
    if (!Array.isArray(flow.steps) || flow.steps.length === 0) errors.push(`${flow.id}: faltan pasos`);
    if (flow.steps?.some((step) => !step.action || !step.expected)) errors.push(`${flow.id}: paso incompleto`);
    if (!Array.isArray(flow.assertions) || flow.assertions.length === 0) errors.push(`${flow.id}: faltan aserciones`);
    if (flow.assertions?.some((assertion) => !assertion.kind || !assertion.expected)) errors.push(`${flow.id}: aserción incompleta`);
    if (!Array.isArray(flow.cleanup)) errors.push(`${flow.id}: cleanup debe ser una lista`);
    if (flow.execution === "deterministic" && (!flow.fixture || !(flow.fixture in (catalog.fixtures?.scenarios ?? {})))) errors.push(`${flow.id}: fixture determinista inexistente`);
  }
  return errors;
}
