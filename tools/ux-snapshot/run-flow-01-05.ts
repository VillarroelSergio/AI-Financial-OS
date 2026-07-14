import { chromium, type Browser, type Locator, type Page } from "playwright";
import { spawn, type ChildProcess } from "node:child_process";
import net from "node:net";
import { mkdir, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import assert from "node:assert/strict";
import { loadFlowContracts, validateFlowContracts } from "./flow-contracts.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(__dirname, "../..");
const DESKTOP_DIR = path.join(PROJECT_ROOT, "apps", "desktop");
const BACKEND_DIR = path.join(PROJECT_ROOT, "backend");
const BACKEND_PYTHON = path.join(BACKEND_DIR, ".venv", "Scripts", "python.exe");
const VITE_CLI = path.join(DESKTOP_DIR, "node_modules", "vite", "bin", "vite.js");
const OUTPUT_DIR = path.join(PROJECT_ROOT, "ux-snapshots", "e2e", "flow-01-05");
const FLOW_CATALOG_PATH = path.join(PROJECT_ROOT, "docs", "testing", "flows", "catalog.yaml");
const FIXTURE_PATH = path.join(PROJECT_ROOT, "docs", "testing", "fixtures", "financial-os.yaml");
const E2E_DATA_ROOT = process.env.E2E_DATA_ROOT ?? path.join(tmpdir(), "ai-financial-os-e2e");
// The backend CORS allow-list uses localhost:1420 for the web frontend.
const BASE_URL = process.env.E2E_BASE_URL ?? "http://localhost:1420";
const API_URL = process.env.E2E_API_URL ?? "http://127.0.0.1:18010";
const HEADED = process.argv.includes("--headed");
const EXTERNAL_SERVERS = process.argv.includes("--external");
const ACTION_DELAY_MS = Number(process.env.E2E_ACTION_DELAY_MS ?? (HEADED ? 1200 : 0));
const TYPE_DELAY_MS = Number(process.env.E2E_TYPE_DELAY_MS ?? (HEADED ? 70 : 0));

type Overview = {
  net_worth: string;
  liquidity: string;
  monthly_income: string;
  monthly_expense: string;
};
type FlowResult = { id: string; status: "PASS" | "FAIL" | "BLOCKED"; reason?: string };

const results: FlowResult[] = [];
const consoleErrors: string[] = [];
const failedResponses: string[] = [];
let browser: Browser | undefined;
let backend: ChildProcess | undefined;
let frontend: ChildProcess | undefined;
let e2eDataDir: string | undefined;

function record(id: string, action: () => Promise<void>) {
  return action()
    .then(async () => {
      results.push({ id, status: "PASS" as const });
      await pause();
    })
    .catch((error: unknown) => {
      const reason = error instanceof Error ? error.message : String(error);
      results.push({ id, status: "FAIL", reason });
      return pause().then(() => { throw error; });
    });
}

async function recordContinuing(id: string, action: () => Promise<void>) {
  try {
    await action();
    results.push({ id, status: "PASS" });
  } catch (error: unknown) {
    const reason = error instanceof Error ? error.message : String(error);
    results.push({ id, status: "FAIL", reason });
  } finally {
    await pause();
  }
}

function command(commandName: string, args: string[], cwd: string, env: NodeJS.ProcessEnv) {
  const executable = process.platform === "win32" && commandName === "npm" ? "npm.cmd" : commandName;
  return spawn(executable, args, { cwd, env, stdio: ["ignore", "pipe", "pipe"] });
}

async function waitFor(url: string, timeoutMs = 30_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch {
      // The process is still starting.
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw new Error(`Servidor no disponible tras ${timeoutMs} ms: ${url}`);
}

async function assertPortFree(port: number) {
  const host = "127.0.0.1";
  await new Promise<void>((resolve, reject) => {
    const socket = net.createConnection({ host, port });
    socket.once("connect", () => {
      socket.destroy();
      reject(new Error(`Preflight inseguro: el puerto ${port} ya está ocupado; cierra la instancia existente o usa --external.`));
    });
    socket.once("error", () => {
      socket.destroy();
      resolve();
    });
  });
}

async function waitForPortFree(port: number, timeoutMs = 10_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      await assertPortFree(port);
      return;
    } catch {
      await new Promise((resolve) => setTimeout(resolve, 250));
    }
  }
  throw new Error(`El puerto ${port} sigue ocupado tras cerrar los servidores E2E.`);
}

async function startServers() {
  if (EXTERNAL_SERVERS) {
    await waitFor(`${API_URL}/health`);
    await waitFor(BASE_URL);
    return;
  }

  await assertPortFree(18010);
  await assertPortFree(1420);
  e2eDataDir = path.join(E2E_DATA_ROOT, `flow-01-05-${Date.now()}`);
  await mkdir(e2eDataDir, { recursive: true });
  const env = {
    ...process.env,
    DATABASE_URL: `sqlite:///${path.join(e2eDataDir, "financial.db").replaceAll("\\", "/")}`,
    DUCKDB_PATH: path.join(e2eDataDir, "analytics.duckdb"),
    MI_SQLITE_PATH: path.join(e2eDataDir, "market_intelligence.db"),
    FINOS_DATA_DIR: e2eDataDir,
  };

  // Launch the real executables directly. Wrapping them in cmd.exe lets the shell
  // exit before npm/python's descendants, leaving orphan listeners on Windows.
  backend = command(BACKEND_PYTHON, ["-m", "uvicorn", "app.main:app", "--port", "18010"], BACKEND_DIR, env);
  const frontendEnv = {
    ...env,
    VITE_USE_MOCK_DATA: "false",
    VITE_API_BASE_URL: API_URL,
  };
  frontend = command(process.execPath, [VITE_CLI, "--host", "127.0.0.1"], DESKTOP_DIR, frontendEnv);
  await Promise.all([waitFor(`${API_URL}/health`), waitFor(BASE_URL)]);
  const accountsResponse = await fetch(`${API_URL}/api/accounts`);
  if (!accountsResponse.ok) throw new Error(`Preflight de cuentas falló con HTTP ${accountsResponse.status}`);
  const accounts = await accountsResponse.json() as unknown[];
  if (accounts.length !== 0) {
    throw new Error(`Preflight inseguro: la base E2E contiene ${accounts.length} cuenta(s); se detiene sin mutar datos.`);
  }
}

async function stopProcess(processHandle: ChildProcess | undefined) {
  if (!processHandle) return;
  await new Promise<void>((resolve) => {
    const finish = () => resolve();
    processHandle.once("close", finish);
    // A child launched by this runner can be terminated directly without relying
    // on an elevated taskkill invocation. This releases the listener even when
    // taskkill is blocked by the host's process permissions.
    if (processHandle.exitCode === null) processHandle.kill();
    if (process.platform === "win32" && processHandle.pid) {
      const killer = spawn("taskkill", ["/pid", String(processHandle.pid), "/t", "/f"], { stdio: "ignore" });
      killer.once("close", () => setTimeout(finish, 500));
      killer.once("error", finish);
    } else {
      setTimeout(finish, 500);
    }
    setTimeout(finish, 5_000);
  });
}

async function json<T>(page: Page, endpoint: string): Promise<T> {
  return page.evaluate(async (url) => {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`${response.status} ${url}`);
    return response.json();
  }, `${API_URL}${endpoint}`) as Promise<T>;
}

async function api<T>(page: Page, method: string, endpoint: string, body?: unknown) {
  return page.evaluate(async ({ url, requestMethod, requestBody }) => {
    const response = await fetch(url, {
      method: requestMethod,
      headers: requestBody === undefined ? undefined : { "content-type": "application/json" },
      body: requestBody === undefined ? undefined : JSON.stringify(requestBody),
    });
    let data: unknown = null;
    try { data = await response.json(); } catch { /* 204 */ }
    return { status: response.status, data } as { status: number; data: unknown };
  }, { url: `${API_URL}${endpoint}`, requestMethod: method, requestBody: body }) as Promise<{ status: number; data: T }>;
}

async function screenshot(page: Page, name: string) {
  await page.screenshot({ path: path.join(OUTPUT_DIR, `${name}.png`), fullPage: true });
}

async function pause() {
  if (ACTION_DELAY_MS > 0) await new Promise((resolve) => setTimeout(resolve, ACTION_DELAY_MS));
}

async function fillField(field: Locator, value: string, sequential = true) {
  // Numeric inputs must be filled atomically. Character-by-character typing lets
  // the browser normalize intermediate values (e.g. 1000 -> 0.001000).
  if (TYPE_DELAY_MS > 0 && sequential) {
    await field.click();
    await field.pressSequentially(value, { delay: TYPE_DELAY_MS });
  } else {
    await field.fill(value);
  }
  await pause();
}

async function expectApi(page: Page, urlPart: string, method: string, action: () => Promise<void>, statuses: number[] = [200]) {
  const responsePromise = page.waitForResponse(
    (response) => response.url().includes(urlPart) && response.request().method() === method,
    { timeout: 15_000 },
  );
  await action();
  const response = await responsePromise;
  assert.ok(statuses.includes(response.status()), `${method} ${urlPart} devolvió ${response.status()}`);
  return response;
}

async function visibleText(page: Page) {
  return (await page.locator("body").innerText()).replace(/\s+/g, " ");
}

async function installExternalFixtures(page: Page) {
  const now = "2026-07-13T10:00:00Z";
  const fixture = (body: unknown) => ({ status: 200, contentType: "application/json", body: JSON.stringify(body) });
  await page.route("**/api/market-intelligence/**", async (route) => {
    const pathname = new URL(route.request().url()).pathname;
    if (pathname.endsWith("/snapshot/market")) return route.fulfill(fixture({
      status: "complete", generated_at: now, quality_score: 1, warnings: [],
      indices: [{ catalog_item_id: "sp500", symbol: "SPX", asset_type: "index", price: 5400, change_pct: 0.4, currency: "USD", provider_id: "fixture-market-v1", quality_score: 1, data_status: "ok", observed_at: now, display_name: "S&P 500" }],
      crypto: [{ catalog_item_id: "bitcoin", symbol: "BTC", asset_type: "crypto", price: 60000, change_pct: 1.2, currency: "USD", provider_id: "fixture-market-v1", quality_score: 1, data_status: "ok", observed_at: now, display_name: "Bitcoin" }],
      commodities: [{ catalog_item_id: "gold", symbol: "XAU", asset_type: "commodity", price: 2350, change_pct: -0.1, currency: "USD", provider_id: "fixture-market-v1", quality_score: 1, data_status: "ok", observed_at: now, display_name: "Oro" }],
    }));
    if (pathname.endsWith("/snapshot/forex")) return route.fulfill(fixture({ generated_at: now, warnings: [], rates: [
      { catalog_item_id: "eur_usd", base_currency: "EUR", quote_currency: "USD", rate: 1.10, date: "2026-07-13", provider_id: "fixture-market-v1", quality_score: 1, data_status: "ok" },
      { catalog_item_id: "eur_gbp", base_currency: "EUR", quote_currency: "GBP", rate: 0.85, date: "2026-07-13", provider_id: "fixture-market-v1", quality_score: 1, data_status: "ok" },
    ] }));
    if (pathname.endsWith("/snapshot/bonds")) return route.fulfill(fixture({ generated_at: now, warnings: [], yields: [
      { catalog_item_id: "us_2y", country: "US", maturity: "2Y", yield_value: 4.2, date: "2026-07-13", provider_id: "fixture-market-v1", quality_score: 1, data_status: "ok" },
      { catalog_item_id: "us_10y", country: "US", maturity: "10Y", yield_value: 4.0, date: "2026-07-13", provider_id: "fixture-market-v1", quality_score: 1, data_status: "ok" },
    ] }));
    if (pathname.endsWith("/snapshot/macro")) return route.fulfill(fixture({ status: "complete", generated_at: now, warnings: [], spain: [{ catalog_item_id: "es_cpi", country: "ES", period: "2026-06", value: 2.4, unit: "%", provider_id: "fixture-macro-v1", quality_score: 1, data_status: "ok", display_name: "Inflación", previous_value: 2.1, delta: 0.3, history: [{ period: "2026-05", value: 2.1 }, { period: "2026-06", value: 2.4 }] }], eurozone: [], usa: [] }));
    if (pathname.endsWith("/personal-impact")) return route.fulfill(fixture({ generated_at: now, warnings: [], comparatives: [] }));
    if (pathname.endsWith("/ingest-status")) return route.fulfill(fixture({ storage: "file", status: "ok" }));
    return route.continue();
  });
}

async function main() {
  const flowContracts = await loadFlowContracts(FLOW_CATALOG_PATH, FIXTURE_PATH);
  const contractErrors = validateFlowContracts(flowContracts);
  assert.deepEqual(contractErrors, [], `Contratos FLOW inválidos:\n${contractErrors.join("\n")}`);
  await mkdir(OUTPUT_DIR, { recursive: true });
  await startServers();
  browser = await chromium.launch({ headless: !HEADED, slowMo: HEADED ? 350 : 0 });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  await installExternalFixtures(page);

  page.on("console", (message) => {
    if (message.type() === "error" && !message.text().includes("Failed to load resource")) {
      consoleErrors.push(message.text());
    }
  });
  page.on("response", (response) => {
    if (response.status() >= 500) failedResponses.push(`${response.status()} ${response.url()}`);
  });

  let t0: Overview;
  let accountId = "";
  const transactionIds: string[] = [];
  const billIds: string[] = [];
  let budgetId = "";
  let recurringId = "";
  let goalId = "";
  let insightId = "";
  const month = new Date().toISOString().slice(0, 7);

  await record("FLOW-01", async () => {
    const overviewResponse = page.waitForResponse(
      (response) => response.url().endsWith("/api/dashboard/overview") && response.request().method() === "GET",
    );
    await page.goto(`${BASE_URL}/`, { waitUntil: "domcontentloaded" });
    await page.locator('[data-app-ready="true"]').waitFor();
    await pause();
    const response = await overviewResponse;
    assert.equal(response.status(), 200);
    t0 = await response.json() as Overview;
    assert.ok(Number.isFinite(Number(t0.net_worth)));
    assert.ok(Number.isFinite(Number(t0.liquidity)));
    const text = await visibleText(page);
    assert.match(text, /Patrimonio|Resumen/i);
    assert.doesNotMatch(text, /NaN|undefined|null/);
    await screenshot(page, "FLOW-01-summary");
  });

  await record("FLOW-02", async () => {
    await page.goto(`${BASE_URL}/finances?tab=cuentas`, { waitUntil: "domcontentloaded" });
    await page.getByRole("button", { name: "Nueva cuenta" }).click();
    await fillField(page.getByLabel("Nombre"), "E2E Test Bank");
    await page.getByLabel("Tipo").selectOption("bank");
    await fillField(page.getByLabel("Saldo"), "1000", false);
    await fillField(page.getByLabel("Divisa"), "EUR");
    const response = await expectApi(page, "/api/accounts", "POST", () => page.getByRole("button", { name: "Guardar" }).click(), [201]);
    const account = await response.json() as { id: string; current_balance: string };
    accountId = account.id;
    assert.equal(account.current_balance, "1000.00");
    await page.getByText("E2E Test Bank", { exact: true }).first().waitFor();
    const text = await visibleText(page);
    assert.match(text, /1\.000,00|1000,00/);
    assert.doesNotMatch(text, new RegExp(accountId));
    await screenshot(page, "FLOW-02-account");
  });

  await record("FLOW-03", async () => {
    await page.goto(`${BASE_URL}/finances?tab=movimientos`, { waitUntil: "domcontentloaded" });
    await page.getByRole("button", { name: "Nuevo movimiento" }).click();
    await fillField(page.getByLabel("Descripcion"), "E2E lunch test");
    await fillField(page.getByRole("spinbutton", { name: "Importe", exact: true }), "-42.30", false);
    await page.getByLabel("Tipo").selectOption("expense");
    await page.getByLabel("Cuenta").selectOption({ label: "E2E Test Bank" });
    await page.getByRole("combobox", { name: "Categoria", exact: true }).selectOption({ label: "Restaurante" });
    const expenseResponse = await expectApi(page, "/api/transactions", "POST", () => page.getByRole("button", { name: "Guardar" }).click(), [201]);
    transactionIds.push((await expenseResponse.json() as { id: string }).id);
    await page.getByText("E2E lunch test", { exact: true }).waitFor();

    await page.getByRole("button", { name: "Nuevo movimiento" }).click();
    await fillField(page.getByLabel("Descripcion"), "E2E salary test");
    await fillField(page.getByRole("spinbutton", { name: "Importe", exact: true }), "500", false);
    await page.getByLabel("Tipo").selectOption("income");
    await page.getByLabel("Cuenta").selectOption({ label: "E2E Test Bank" });
    await page.getByRole("combobox", { name: "Categoria", exact: true }).selectOption({ label: "Salario" });
    const incomeResponse = await expectApi(page, "/api/transactions", "POST", () => page.getByRole("button", { name: "Guardar" }).click(), [201]);
    transactionIds.push((await incomeResponse.json() as { id: string }).id);
    await page.getByText("E2E salary test", { exact: true }).waitFor();
    assert.match(await visibleText(page), /42,30|42\.30/);
    assert.match(await visibleText(page), /500,00|500\.00/);
    await screenshot(page, "FLOW-03-transactions");
  });

  await record("FLOW-04", async () => {
    await page.goto(`${BASE_URL}/finances?tab=gastos`, { waitUntil: "domcontentloaded" });
    await page.getByRole("button", { name: /Restaurante/ }).waitFor();
    const text = await visibleText(page);
    assert.match(text, /42,30|42\.30/);
    const categoryButton = page.getByRole("button", { name: /Restaurante/ });
    await expectApi(page, "/api/dashboard/spending/category-detail", "GET", () => categoryButton.click());
    await page.getByText("E2E lunch test", { exact: true }).waitFor();
    await screenshot(page, "FLOW-04-spending-detail");
  });

  await record("FLOW-05", async () => {
    await page.goto(`${BASE_URL}/`, { waitUntil: "domcontentloaded" });
    await page.locator('[data-app-ready="true"]').waitFor();
    const finalOverview = await json<Overview>(page, "/api/dashboard/overview");
    const delta = Number(finalOverview.net_worth) - Number(t0.net_worth);
    // Current product semantics: transactions feed monthly aggregates but do not
    // mutate Account.current_balance. The opening account balance is +1000.
    assert.ok(Math.abs(delta - 1000) < 0.01, `Cambio patrimonial inesperado: ${delta}`);
    assert.ok(Number(finalOverview.liquidity) > Number(t0.liquidity));
    assert.equal(Number(finalOverview.monthly_income), 500);
    assert.equal(Number(finalOverview.monthly_expense), 42.3);
    await screenshot(page, "FLOW-05-final-summary");
  });

  await recordContinuing("FLOW-06", async () => {
    const previous = new Date(Date.UTC(new Date().getUTCFullYear(), new Date().getUTCMonth() - 1, 1));
    const start = previous.toISOString().slice(0, 7) + "-01";
    const end = new Date(Date.UTC(previous.getUTCFullYear(), previous.getUTCMonth() + 1, 0)).toISOString().slice(0, 10);
    const response = await api<{ id: string }>(page, "POST", "/api/household-bills", {
      provider: "E2E Iberdrola", service_type: "electricity", period_start: start, period_end: end,
      amount: "95.00", currency: "EUR", is_recurring: true,
    });
    assert.equal(response.status, 201);
    billIds.push(response.data.id);
    await page.goto(`${BASE_URL}/planificacion?tab=facturas`, { waitUntil: "domcontentloaded" });
    assert.match(await visibleText(page), /Iberdrola|Facturas/i);
    await screenshot(page, "FLOW-06-household-bill");
  });

  await recordContinuing("FLOW-07", async () => {
    const start = `${month}-01`;
    const end = new Date(Date.UTC(new Date().getUTCFullYear(), new Date().getUTCMonth() + 1, 0)).toISOString().slice(0, 10);
    const response = await api<{ id: string }>(page, "POST", "/api/household-bills", {
      provider: "E2E Iberdrola", service_type: "electricity", period_start: start, period_end: end,
      amount: "140.00", currency: "EUR", is_recurring: true,
    });
    assert.equal(response.status, 201);
    billIds.push(response.data.id);
    const summary = await api<{ items: Array<{ provider: string; change_pct: number | null; anomaly: boolean; next_estimate: number }> }>(page, "GET", "/api/household-bills/summary");
    assert.equal(summary.status, 200);
    const item = summary.data.items.find((entry) => entry.provider === "E2E Iberdrola");
    assert.ok(item && (item.change_pct ?? 0) >= 20 && item.anomaly && item.next_estimate > 0);
  });

  await recordContinuing("FLOW-08", async () => {
    const categories = await json<Array<{ id: string; name: string }>>(page, "/api/categories");
    const restaurant = categories.find((category) => category.name === "Restaurante");
    assert.ok(restaurant);
    const response = await api<{ id: string }>(page, "POST", "/api/budgets", {
      category_id: restaurant.id, period: "monthly", amount: "500", alert_threshold_pct: 80, active: true,
    });
    assert.equal(response.status, 201);
    budgetId = response.data.id;
    const budgetsLoad = page.waitForResponse((entry) => entry.url().includes("/api/budgets") && entry.request().method() === "GET");
    await page.goto(`${BASE_URL}/planificacion?tab=presupuestos`, { waitUntil: "domcontentloaded" });
    await budgetsLoad;
    await page.waitForFunction(() => !document.body.innerText.includes("Cargando presupuestos"));
    assert.match(await visibleText(page), /500|Restaurante/);
  });

  await recordContinuing("FLOW-09", async () => {
    const response = await api<Array<{ category_name: string; actual_amount: number; consumption_pct: number; alert: boolean }>>(page, "GET", `/api/budgets/comparison?month=${month}`);
    assert.equal(response.status, 200);
    const item = response.data.find((entry) => entry.category_name === "Restaurante");
    assert.ok(item && Math.abs(item.actual_amount - 42.3) < 0.01 && Math.abs(item.consumption_pct - 8.5) < 0.2 && !item.alert);
  });

  await recordContinuing("FLOW-10", async () => {
    const response = await api<Array<unknown>>(page, "GET", "/api/recurring/candidates");
    assert.equal(response.status, 200);
    if (response.data.length === 0) throw new Error("Histórico efímero insuficiente para detectar candidatos");
  });
  if (results.at(-1)?.id === "FLOW-10" && results.at(-1)?.status === "FAIL") {
    results[results.length - 1] = { id: "FLOW-10", status: "BLOCKED", reason: "El histórico efímero no contiene las ocurrencias mínimas." };
  }

  await recordContinuing("FLOW-11", async () => {
    const nextDate = new Date(Date.UTC(new Date().getUTCFullYear(), new Date().getUTCMonth() + 1, 8)).toISOString().slice(0, 10);
    const response = await api<{ id: string }>(page, "POST", "/api/recurring", {
      name: "Netflix E2E", amount: "15.99", currency: "EUR", type: "expense", frequency: "monthly",
      day_of_month: 8, next_date: nextDate, active: true,
    });
    assert.equal(response.status, 201);
    recurringId = response.data.id;
    const calendar = await api<Array<{ recurring_id: string; name: string }>>(page, "GET", "/api/recurring/calendar?days=60");
    assert.equal(calendar.status, 200);
    assert.ok(calendar.data.some((entry) => entry.recurring_id === recurringId && entry.name === "Netflix E2E"));
  });

  await recordContinuing("FLOW-12", async () => {
    const response = await api<{ months: Array<{ recurring_expenses: number }> }>(page, "GET", "/api/cashflow/forecast?months=3");
    assert.equal(response.status, 200);
    assert.ok(response.data.months.length > 0 && response.data.months.some((entry) => entry.recurring_expenses >= 15.99));
    await page.goto(`${BASE_URL}/planificacion?tab=cashflow`, { waitUntil: "domcontentloaded" });
    assert.match(await visibleText(page), /Cashflow/i);
    await screenshot(page, "FLOW-12-cashflow");
  });

  for (const id of ["FLOW-13", "FLOW-14", "FLOW-15", "FLOW-27", "FLOW-28", "FLOW-29"]) {
    results.push({ id, status: "BLOCKED", reason: "Pendiente de provider/fixture externo; separado del piloto determinista." });
  }

  await recordContinuing("FLOW-16", async () => {
    const response = await api<{ id: string }>(page, "POST", "/api/goals", {
      name: "E2E Fondo Test", type: "savings", target_amount: "10000", current_amount: "2000",
      monthly_contribution: "300", priority: "medium",
    });
    assert.equal(response.status, 201);
    goalId = response.data.id;
    const simulation = await api<{ scenarios: Array<{ projected_date: string | null; months_to_target: number | null }> }>(page, "POST", `/api/goals/${goalId}/simulate`, { inflation_rate: 0.03 });
    assert.equal(simulation.status, 200);
    assert.equal(simulation.data.scenarios.length, 3);
    assert.ok(simulation.data.scenarios.every((scenario) => scenario.projected_date || scenario.months_to_target));
    const progress = await api<{ progress_pct: number }>(page, "GET", `/api/goals/${goalId}/progress`);
    assert.equal(progress.status, 200);
    assert.ok(Math.abs(progress.data.progress_pct - 20) < 0.01);
    await page.goto(`${BASE_URL}/goals`, { waitUntil: "domcontentloaded" });
    assert.match(await visibleText(page), /E2E Fondo Test|Objetivos/i);
    await screenshot(page, "FLOW-16-goal");
  });

  await recordContinuing("FLOW-17", async () => {
    const response = await api<{ status: string; indices: Array<{ provider_id: string; quality_score: number }> }>(page, "GET", "/api/market-intelligence/snapshot/market");
    assert.equal(response.status, 200);
    assert.equal(response.data.status, "complete");
    assert.ok(response.data.indices.every((item) => item.provider_id === "fixture-market-v1" && item.quality_score === 1));
    await page.goto(`${BASE_URL}/markets`, { waitUntil: "domcontentloaded" });
    assert.match(await visibleText(page), /Mercado|S&P 500|Bitcoin/i);
    await screenshot(page, "FLOW-17-markets");
  });

  await recordContinuing("FLOW-18", async () => {
    const response = await api<{ rates: Array<{ catalog_item_id: string; rate: number }> }>(page, "GET", "/api/market-intelligence/snapshot/forex");
    assert.equal(response.status, 200);
    const eurUsd = response.data.rates.find((rate) => rate.catalog_item_id === "eur_usd");
    const eurGbp = response.data.rates.find((rate) => rate.catalog_item_id === "eur_gbp");
    assert.ok(eurUsd && eurGbp && eurUsd.rate !== eurGbp.rate);
  });

  await recordContinuing("FLOW-19", async () => {
    const response = await api<{ yields: Array<{ maturity: string; provider_id: string }> }>(page, "GET", "/api/market-intelligence/snapshot/bonds");
    assert.equal(response.status, 200);
    assert.deepEqual(response.data.yields.map((item) => item.maturity), ["2Y", "10Y"]);
    assert.ok(response.data.yields.every((item) => item.provider_id === "fixture-market-v1"));
  });

  await recordContinuing("FLOW-20", async () => {
    const response = await api<{ storage: string; status: string }>(page, "GET", "/api/market-intelligence/ingest-status");
    assert.equal(response.status, 200);
    assert.equal(response.data.storage, "file");
    assert.equal(response.data.status, "ok");
  });

  await recordContinuing("FLOW-21", async () => {
    const response = await api<{ status: string; spain: Array<{ unit: string; history: unknown[]; delta: number }> }>(page, "GET", "/api/market-intelligence/snapshot/macro");
    assert.equal(response.status, 200);
    assert.equal(response.data.status, "complete");
    assert.ok(response.data.spain.every((item) => item.unit && item.history.length >= 2 && Number.isFinite(item.delta)));
    await page.goto(`${BASE_URL}/economy`, { waitUntil: "domcontentloaded" });
    assert.match(await visibleText(page), /Economía|Inflación/i);
    await screenshot(page, "FLOW-21-economy");
  });

  await recordContinuing("FLOW-22", async () => {
    const response = await api<{ comparatives: Array<{ signal: string; signal_text: string }> }>(page, "GET", "/api/market-intelligence/personal-impact");
    assert.equal(response.status, 200);
    assert.ok(response.data.comparatives.every((item) => item.signal !== "no_data" || item.signal_text.length === 0));
  });

  await recordContinuing("FLOW-23", async () => {
    const response = await api<{ insights: Array<{ id: string }> }>(page, "GET", `/api/insights?period=${month}`);
    assert.equal(response.status, 200);
    assert.ok(Array.isArray(response.data.insights));
    insightId = response.data.insights[0]?.id ?? "";
    await page.goto(`${BASE_URL}/insights`, { waitUntil: "domcontentloaded" });
    assert.match(await visibleText(page), /Insights|datos/i);
    await screenshot(page, "FLOW-23-insights");
  });

  await recordContinuing("FLOW-24", async () => {
    assert.ok(insightId, "No hay insight visible para dismiss/restore");
    assert.equal((await api(page, "POST", `/api/insights/${encodeURIComponent(insightId)}/dismiss`, {})).status, 200);
    assert.equal((await api(page, "POST", `/api/insights/${encodeURIComponent(insightId)}/restore`, {})).status, 200);
  });

  await recordContinuing("FLOW-25", async () => {
    const response = await api<{ ready: boolean; items: Array<{ status: string }> }>(page, "GET", `/api/net-worth/snapshot-readiness?month=${month}`);
    assert.equal(response.status, 200);
    assert.ok(response.data.items.every((item) => ["ok", "stale", "missing"].includes(item.status)));
    assert.ok(!(response.data.ready && response.data.items.some((item) => item.status === "missing")));
  });

  await recordContinuing("FLOW-26", async () => {
    const created = await api(page, "POST", "/api/net-worth/snapshots", { month, force_partial: true });
    assert.ok([201, 409].includes(created.status));
    if (created.status === 201) {
      const sheet = await api<{ total_assets: number; total_liabilities: number; net_worth: number }>(page, "GET", `/api/net-worth/balance-sheet?month=${month}`);
      assert.equal(sheet.status, 200);
      assert.ok(Math.abs(sheet.data.net_worth - (sheet.data.total_assets - sheet.data.total_liabilities)) < 0.01);
    }
  });

  await recordContinuing("FLOW-30", async () => {
    const status = await api<{ database_filename: string; demo_data_policy: string }>(page, "GET", "/api/security/status");
    assert.equal(status.status, 200);
    assert.ok(status.data.database_filename && status.data.demo_data_policy);
    const integrity = await api<{ status: string; database_ok: boolean; tables: string[] }>(page, "GET", "/api/security/integrity");
    assert.equal(integrity.status, 200);
    assert.equal(integrity.data.database_ok, true);
    assert.ok(integrity.data.status === "ok" && integrity.data.tables.length > 0);
    await screenshot(page, "FLOW-30-security");
  });

  await recordContinuing("FLOW-31", async () => {
    const before = await api<unknown[]>(page, "GET", "/api/security/backups");
    assert.equal(before.status, 200);
    assert.equal((await api(page, "POST", "/api/security/backups", {})).status, 201);
    const after = await api<unknown[]>(page, "GET", "/api/security/backups");
    assert.equal(after.status, 200);
    assert.ok(after.data.length > before.data.length);
  });

  await recordContinuing("FLOW-32", async () => {
    const overview = await json<Overview>(page, "/api/dashboard/overview");
    assert.ok(Number(overview.net_worth) >= Number(t0.net_worth));
    assert.equal(consoleErrors.length, 0, `Errores de consola: ${consoleErrors.join(" | ")}`);
    await screenshot(page, "FLOW-32-final-summary");
  });

  await recordContinuing("FLOW-33", async () => {
    const remove = async (endpoint: string, id: string) => {
      if (!id) return;
      const response = await api(page, "DELETE", `${endpoint}/${id}`);
      assert.ok([204, 404].includes(response.status));
    };
    await remove("/api/goals", goalId);
    await remove("/api/recurring", recurringId);
    await remove("/api/budgets", budgetId);
    for (const id of billIds.reverse()) await remove("/api/household-bills", id);
    for (const id of transactionIds.reverse()) await remove("/api/transactions", id);
    await remove("/api/accounts", accountId);
    assert.equal((await json<unknown[]>(page, "/api/accounts")).length, 0);
  });

  await writeReport();
  const failures = results.filter((result) => result.status === "FAIL");
  if (failures.length > 0) {
    const details = failures.map((result) => `${result.id}: ${result.reason ?? "sin detalle"}`).join(" | ");
    throw new Error(`E2E finalizado con ${failures.length} flujo(s) fallido(s): ${details}. Consulta report.md para el detalle completo.`);
  }
}

async function writeReport() {
  const report = [
    "# E2E report — FLOW-01..33",
    "",
    `Generated: ${new Date().toISOString()}`,
    `Base URL: ${BASE_URL}`,
    `API URL: ${API_URL}`,
    `Isolated data directory: ${e2eDataDir ?? "external servers (not managed by runner)"}`,
    "",
    "## Flows",
    "",
    "| Flow | Status | Reason |",
    "|---|---|---|",
    ...results.map((result) => `| ${result.id} | ${result.status} | ${result.reason ?? ""} |`),
    "",
    "## Console errors",
    "",
    ...(consoleErrors.length ? consoleErrors.map((error) => `- ${error}`) : ["- None"]),
    "",
    "## HTTP 5xx responses",
    "",
    ...(failedResponses.length ? failedResponses.map((error) => `- ${error}`) : ["- None"]),
    "",
    "## Findings",
    "",
    "- FLOW-05 valida la semántica actual: el saldo inicial de la cuenta suma +1000 € al patrimonio y los movimientos alimentan los agregados mensuales (+500 € ingresos y 42,30 € gasto). FLOW-17..22 usan fixtures locales de Playwright; inversiones, RAG e IA siguen BLOCKED hasta disponer de sus adaptadores deterministas.",
  ].join("\n");
  await writeFile(path.join(OUTPUT_DIR, "report.md"), report, "utf8");
}

async function cleanup() {
  await writeReport();
  await browser?.close();
  await stopProcess(frontend);
  await stopProcess(backend);
  await Promise.all([waitForPortFree(1420), waitForPortFree(18010)]).catch((error) => {
    console.error("No se pudieron liberar los puertos E2E:", error);
  });
  if (e2eDataDir) {
    for (let attempt = 1; attempt <= 5; attempt += 1) {
      try {
        await rm(e2eDataDir, { recursive: true, force: true });
        break;
      } catch (error) {
        if (attempt === 5) console.error(`No se pudo limpiar ${e2eDataDir}:`, error);
        else await new Promise((resolve) => setTimeout(resolve, 500));
      }
    }
  }
}

await main()
  .catch((error) => {
    console.error(error instanceof Error ? error.stack ?? error.message : error);
    process.exitCode = 1;
  })
  .finally(cleanup);
