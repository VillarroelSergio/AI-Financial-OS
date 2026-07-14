import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { getMockResponse } from "../../apps/desktop/src/lib/api/mock-data";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "../..");

async function source(relativePath: string): Promise<string> {
  return readFile(path.join(ROOT, relativePath), "utf8");
}

const [rootLayout, dashboardUi, metricCard, spending, goals, budgetCard, assistantPage, analysisCenter, assistantMessages, appRoutes, planningPage, budgetTab, marketsPage, accountsPage, settingsPage, economyPage, indicatorCard, impactCard, personalEconomy, chartPalette, viteConfig, categoryTabs, regionTabs, appCss, snapshotRoutes] = await Promise.all([
  source("apps/desktop/src/app/layout/RootLayout.tsx"),
  source("apps/desktop/src/components/ui/Dashboard.tsx"),
  source("apps/desktop/src/components/ui/MetricCard.tsx"),
  source("apps/desktop/src/features/spending/SpendingPage.tsx"),
  source("apps/desktop/src/features/goals/GoalsPage.tsx"),
  source("apps/desktop/src/features/planning/BudgetCard.tsx"),
  source("apps/desktop/src/features/assistant/AssistantPage.tsx"),
  source("apps/desktop/src/features/assistant/components/AnalysisCenter.tsx"),
  source("apps/desktop/src/features/assistant/components/AiMessageList.tsx"),
  source("apps/desktop/src/App.tsx"),
  source("apps/desktop/src/pages/PlanificacionPage.tsx"),
  source("apps/desktop/src/features/planning/BudgetTab.tsx"),
  source("apps/desktop/src/features/markets/MarketsPage.tsx"),
  source("apps/desktop/src/features/accounts/AccountsPage.tsx"),
  source("apps/desktop/src/features/settings/SettingsPage.tsx"),
  source("apps/desktop/src/features/economy/EconomyPage.tsx"),
  source("apps/desktop/src/features/economy/components/IndicatorCard.tsx"),
  source("apps/desktop/src/features/economy/components/ImpactCard.tsx"),
  source("apps/desktop/src/features/economy/components/PersonalEconomySection.tsx"),
  source("apps/desktop/src/lib/chartPalette.ts"),
  source("apps/desktop/vite.config.ts"),
  source("apps/desktop/src/features/markets/components/CategoryTabs.tsx"),
  source("apps/desktop/src/features/economy/components/RegionTabs.tsx"),
  source("apps/desktop/src/index.css"),
  source("tools/ux-snapshot/snapshot-routes.ts"),
]);

const primaryNav = rootLayout.match(/const navItems:[\s\S]*?\n\];/)?.[0] ?? "";
const routePreloaders = await source("apps/desktop/src/app/routes/pageLoaders.ts");
assert.equal((primaryNav.match(/\{\s*to:/g) ?? []).length, 5, "La navegacion principal debe conservar solo cinco secciones");
assert.doesNotMatch(primaryNav, /\/goals|\/insights/, "Objetivos e Insights no deben aparecer en el menu principal");
assert.doesNotMatch(rootLayout, /initial=\{\{\s*opacity:\s*0,\s*y:/, "La navegacion frecuente no debe desplazar verticalmente la pagina");

assert.doesNotMatch(metricCard, /financial-number[^\n]*truncate/, "Las metricas financieras no deben truncarse");
assert.doesNotMatch(dashboardUi, /financial-number[^\n]*truncate/, "Los KPI financieros no deben truncarse");
assert.match(dashboardUi, /sanitizeUserError/, "Los estados de error deben ocultar detalles internos");

for (const [name, contents] of [
  ["SpendingPage", spending],
  ["GoalsPage", goals],
  ["BudgetCard", budgetCard],
] as const) {
  assert.doesNotMatch(contents, /transition-all/, `${name} debe animar solo propiedades explicitas`);
}

assert.match(assistantMessages, /prefers-reduced-motion/, "El scroll del asistente debe respetar movimiento reducido");
assert.match(assistantPage, /page-shell/, "El asistente debe compartir la alineacion del resto de pantallas");
assert.match(assistantPage, /Asistente financiero/, "El asistente debe explicar su proposito desde la cabecera");
assert.match(analysisCenter, /onOpenChat/, "El estado inicial de analisis debe ofrecer continuidad directa hacia el chat");
assert.match(analysisCenter, /<EmptyState/, "El estado inicial del analisis debe usar el patron vacio comun");
assert.match(goals, /goals\.length\s*>\s*0/, "Objetivos no debe duplicar su CTA principal cuando esta vacio");
assert.match(appCss, /\.ui-pressable:active/, "Los controles interactivos deben ofrecer feedback tactil comun");
assert.match(appCss, /prefers-reduced-motion[\s\S]*\.ui-pressable/, "El feedback tactil debe respetar movimiento reducido");
for (const [name, contents] of [
  ["AccountsPage", accountsPage],
  ["SettingsPage", settingsPage],
  ["MarketsPage", marketsPage],
  ["CategoryTabs", categoryTabs],
  ["RegionTabs", regionTabs],
] as const) {
  assert.match(contents, /ui-pressable/, `${name} debe usar el feedback tactil comun en sus controles`);
  assert.doesNotMatch(contents, /transition-all/, `${name} no debe usar transiciones globales en controles frecuentes`);
}
assert.match(appRoutes, /LegacyFinancesRedirect/, "Las rutas antiguas deben conservar su estado al redirigir");
assert.match(planningPage, /planningTab/, "La subseccion de planificacion debe persistir en la URL");
assert.match(budgetTab, /<ErrorState/, "Planificacion debe usar el estado de error seguro y consistente");

const overview = getMockResponse<{ net_worth: string }>("/api/dashboard/overview");
const balance = getMockResponse<{ net_worth: string }>("/api/net-worth/balance-sheet?month=2026-07");
assert.equal(balance.net_worth, overview.net_worth, "El patrimonio destacado y el balance deben usar una cifra coherente");
assert.ok(Array.isArray(getMockResponse("/api/budgets/comparison")), "Planificacion debe disponer de datos de demostracion validos");
assert.match(marketsPage, /searchParams\.get\("region"\)/, "Mercados debe reflejar el filtro regional de la URL");
assert.match(snapshotRoutes, /\/markets\?region=eu/, "La captura europea debe activar un estado visual distinto");
assert.match(appRoutes, /lazy\(/, "Las pantallas de producto deben cargarse bajo demanda");
assert.match(appRoutes, /Suspense/, "Las rutas diferidas deben tener un limite de carga");
assert.match(appRoutes, /warmCoreRoutes/, "Las rutas principales deben precargarse durante el reposo inicial");
assert.match(rootLayout, /preloadRoute/, "La navegacion debe precargar la ruta al acercarse el usuario");
assert.match(routePreloaders, /requestIdleCallback/, "La precarga debe ejecutarse fuera de la interaccion inicial");
assert.match(routePreloaders, /\/finances[\s\S]*\/investments[\s\S]*\/economy[\s\S]*\/markets/, "Los cinco modulos principales deben estar cubiertos por la precarga");
assert.match(viteConfig, /manualChunks/, "La compilacion debe separar proveedores pesados en chunks propios");
assert.match(spending, /useFinancialChartColors/, "La grafica de gastos debe usar una paleta financiera dedicada");
assert.doesNotMatch(spending, /useChartPalette/, "La grafica de gastos no debe heredar la paleta verde y azul generica");
assert.match(chartPalette, /useFinancialChartColors/, "La paleta financiera debe centralizar sus colores");
assert.match(chartPalette, /#2D7B6A/, "La paleta financiera debe usar el verde jade para ingresos");
assert.match(chartPalette, /#B34D62/, "La paleta financiera debe usar el rojo cassis para gastos");
assert.match(chartPalette, /#8FA88D/, "La paleta financiera debe usar salvia para el ahorro");
assert.doesNotMatch(chartPalette, /#B79A45|#98465B|#C9B27A/, "La paleta financiera no debe conservar oro, granate y arena");
assert.match(indicatorCard, /--economy-accent/, "Los indicadores macro deben compartir un unico acento visual");
assert.doesNotMatch(indicatorCard, /emerald|rose|amber/, "Los indicadores macro no deben mezclar acentos arbitrarios");
assert.doesNotMatch(impactCard, /accent-success|amber-400/, "Los impactos macro deben usar la paleta economica comun");
assert.doesNotMatch(personalEconomy, /emerald|red-300|amber-300/, "La economia personal debe reutilizar los tonos economicos semanticos");
assert.doesNotMatch(economyPage, /amber-400/, "Las alertas de Economia deben conservar la paleta unificada");
assert.doesNotMatch(settingsPage, /<Spinner|if \(loading\)/, "Ajustes debe pintar su estructura inmediatamente, sin bloquear en un spinner");
assert.match(appCss, /--economy-accent/, "Los tokens de Economia deben declararse por tema");
assert.match(appCss, /--bg-card:\s*#E7E8E6/, "El tema claro debe usar una superficie gris suave, no blanco puro");
assert.match(appCss, /--positive:\s*#2D7B6A/, "El tema claro debe usar el verde jade como positivo global");
assert.match(appCss, /--negative:\s*#B34D62/, "El tema claro debe usar el rojo cassis como negativo global");
assert.match(appCss, /--positive:\s*#6FC5AE/, "El tema oscuro debe mantener el verde jade con contraste suficiente");
assert.match(appCss, /--negative:\s*#F092A3/, "El tema oscuro debe mantener el rojo cassis con contraste suficiente");

console.log("UI quality contracts: PASS");
