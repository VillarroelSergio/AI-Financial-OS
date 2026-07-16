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

const [rootLayout, financesPage, dashboardUi, metricCard, spending, goals, budgetCard, assistantPage, analysisCenter, assistantMessages, appRoutes, startupExperience, tauriBootstrap, planningPage, budgetTab, marketsPage, accountsPage, settingsPage, economyPage, indicatorCard, impactCard, personalEconomy, chartPalette, viteConfig, tailwindConfig, categoryTabs, regionTabs, appCss, snapshotRoutes, tauriConfig, tauriCapabilities, mainEntry, indexHtml] = await Promise.all([
  source("apps/desktop/src/app/layout/RootLayout.tsx"),
  source("apps/desktop/src/features/finances/FinancesPage.tsx"),
  source("apps/desktop/src/components/ui/Dashboard.tsx"),
  source("apps/desktop/src/components/ui/MetricCard.tsx"),
  source("apps/desktop/src/features/spending/SpendingPage.tsx"),
  source("apps/desktop/src/features/goals/GoalsPage.tsx"),
  source("apps/desktop/src/features/planning/BudgetCard.tsx"),
  source("apps/desktop/src/features/assistant/AssistantPage.tsx"),
  source("apps/desktop/src/features/assistant/components/AnalysisCenter.tsx"),
  source("apps/desktop/src/features/assistant/components/AiMessageList.tsx"),
  source("apps/desktop/src/App.tsx"),
  source("apps/desktop/src/app/StartupExperience.tsx"),
  source("apps/desktop/src-tauri/src/lib.rs"),
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
  source("apps/desktop/tailwind.config.ts"),
  source("apps/desktop/src/features/markets/components/CategoryTabs.tsx"),
  source("apps/desktop/src/features/economy/components/RegionTabs.tsx"),
  source("apps/desktop/src/index.css"),
  source("tools/ux-snapshot/snapshot-routes.ts"),
  source("apps/desktop/src-tauri/tauri.conf.json"),
  source("apps/desktop/src-tauri/capabilities/default.json"),
  source("apps/desktop/src/main.tsx"),
  source("apps/desktop/index.html"),
]);

const primaryNav = rootLayout.match(/const navItems:[\s\S]*?\n\];/)?.[0] ?? "";
assert.equal((primaryNav.match(/\{\s*to:/g) ?? []).length, 5, "La navegacion principal debe conservar solo cinco secciones");
assert.doesNotMatch(primaryNav, /\/goals|\/insights/, "Objetivos e Insights no deben aparecer en el menu principal");
assert.doesNotMatch(rootLayout, /initial=\{\{\s*opacity:\s*0,\s*y:/, "La navegacion frecuente no debe desplazar verticalmente la pagina");
assert.doesNotMatch(rootLayout, /sectionTitle|hidden h-14 shrink-0/, "El escritorio no debe repetir el titulo de la seccion en una barra superior");
assert.doesNotMatch(financesPage, /sticky top-0 z-10 border-b/, "Las pestanas financieras no deben introducir un divisor horizontal redundante");

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
assert.match(appCss, /button:not\(:disabled\):active/, "Los botones heredados deben conservar feedback tactil");
assert.match(appCss, /\.bg-surface-card/, "Las superficies de tarjeta heredadas deben compartir microinteraccion");
assert.match(appCss, /@keyframes card-rise-in/, "Todas las tarjetas deben conservar su entrada desde abajo");
assert.match(appCss, /card-rise-in[\s\S]*prefers-reduced-motion[\s\S]*animation:\s*none/, "La entrada de tarjetas debe respetar movimiento reducido");
assert.match(appCss, /@keyframes allocation-reveal/, "Las barras de asignacion deben revelarse al cambiar de vista");
assert.match(appCss, /text-\\\[10px\\\][\s\S]*var\(--font-scale\)/, "Los tamaños arbitrarios deben responder al ajuste global");
assert.match(tailwindConfig, /"body-md":\s*\["calc\(17px \* var\(--font-scale\)\)"/, "Los tamaños compartidos deben responder al ajuste global");
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
assert.match(appRoutes, /<StartupExperience\s*\/>/, "La animacion acordada debe montarse en cada arranque");
assert.match(startupExperience, /app-launch-stage/, "La experiencia de inicio debe conservar su escenario animado");
assert.match(appCss, /app-launch-stage-exit 2400ms/, "La animacion de inicio debe durar 2,4 segundos");
assert.doesNotMatch(appRoutes, /lazy\(|Suspense|warmCoreRoutes/, "El arranque no debe volver a diferir las pantallas de producto");
assert.match(tauriBootstrap, /main_window\.maximize\(\)/, "La ventana debe abrir maximizada por defecto");
assert.match(tauriConfig, /"visible":\s*false/, "La ventana debe permanecer oculta hasta que la interfaz inicial este montada");
assert.match(tauriConfig, /"backgroundColor":\s*"#111113"/, "El WebView debe nacer con fondo grafito, nunca blanco");
assert.match(tauriCapabilities, /core:window:allow-show/, "El frontend debe poder revelar la ventana preparada");
assert.match(mainEntry, /getCurrentWindow\(\)\.show\(\)/, "La ventana debe mostrarse despues de montar React");
assert.match(indexHtml, /background:\s*#111113/, "El HTML inicial debe conservar el fondo grafito de respaldo");
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
