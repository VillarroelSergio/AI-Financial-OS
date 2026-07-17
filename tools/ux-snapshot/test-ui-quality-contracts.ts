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

const [rootLayout, motionSystem, financesPage, transactionsPage, categoryBadge, dashboardUi, metricCard, spending, goals, budgetCard, assistantPage, analysisCenter, assistantMessages, appRoutes, startupExperience, tauriBootstrap, planningPage, budgetTab, marketsPage, accountsPage, settingsPage, economyPage, indicatorCard, impactCard, personalEconomy, chartPalette, viteConfig, tailwindConfig, categoryTabs, regionTabs, appCss, snapshotRoutes, tauriConfig, tauriCapabilities, mainEntry, indexHtml] = await Promise.all([
  source("apps/desktop/src/app/layout/RootLayout.tsx"),
  source("apps/desktop/src/components/ui/motion.tsx"),
  source("apps/desktop/src/features/finances/FinancesPage.tsx"),
  source("apps/desktop/src/features/transactions/TransactionsPage.tsx"),
  source("apps/desktop/src/components/ui/CategoryBadge.tsx"),
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
assert.match(appCss, /card-rise-in[\s\S]*prefers-reduced-motion[\s\S]*reduced-motion-enter/, "La entrada de tarjetas debe reducirse a un fundido accesible");
assert.match(motionSystem, /contentEnter[\s\S]*opacity:\s*0,\s*y:\s*6[\s\S]*opacity:\s*1,\s*y:\s*0/, "Las paginas deben entrar desde opacidad cero hasta su posicion final");
assert.match(motionSystem, /staggerItem[\s\S]*opacity:\s*0,\s*y:\s*4[\s\S]*opacity:\s*1,\s*y:\s*0/, "Los elementos escalonados deben usar una entrada sutil");
assert.match(rootLayout, /motion\.div[^>]*variants=\{contentEnter\}[^>]*initial="hidden"[^>]*animate="show"/, "Todas las rutas deben compartir la transicion de contenido");
assert.match(appCss, /\.fixed\.inset-0\.z-50[\s\S]*surface-enter/, "Dialogos y drawers deben compartir entrada por opacidad y posicion");
assert.match(appCss, /tbody\s*>\s*tr[\s\S]*row-enter/, "Las filas deben aparecer con el patron sutil comun");
assert.match(appCss, /@keyframes content-enter\s*\{[\s\S]*opacity:\s*0[\s\S]*opacity:\s*1/, "Popovers y avisos deben completar su fundido hasta opacidad total");
const rowEntry = appCss.match(/@keyframes row-enter[\s\S]*?(?=@keyframes scrim-enter)/)?.[0] ?? "";
const progressEntry = appCss.match(/@keyframes progress-reveal[\s\S]*?(?=@keyframes allocation-reveal)/)?.[0] ?? "";
const cardEntryRule = appCss.match(/\/\* Las pantallas usan tres superficies[\s\S]*?(?=\/\* Escalonado local)/)?.[0] ?? "";
assert.doesNotMatch(rowEntry, /transform/, "Las filas de tabla no deben animar transform porque altera su renderizado");
assert.match(progressEntry, /clip-path/, "Las barras deben revelarse sin sobrescribir el porcentaje almacenado en transform");
assert.doesNotMatch(progressEntry, /transform/, "La animacion de progreso no debe forzar scaleX(1)");
assert.doesNotMatch(cardEntryRule, /will-change/, "Las tarjetas no deben crear contextos de apilado permanentes");
assert.match(transactionsPage, /showFilters\s*\?\s*"z-40"/, "El filtro de movimientos debe elevar su contenedor mientras esta abierto");
assert.match(transactionsPage, /<CategoryBadge category=\{categoryFor\(tx\.category_id\)\}/, "La tabla de movimientos debe representar cada categoria con el patron accesible comun");
assert.match(categoryBadge, /data-category-visual/, "Las categorias deben exponer una senal visual reutilizable");
assert.match(categoryBadge, /aria-hidden="true"[\s\S]*<Icon/, "El icono decorativo no debe duplicar el nombre para lectores de pantalla");
assert.match(categoryBadge, /category\?\.name \?\? "Sin categoría"/, "Las categorias deben conservar siempre una etiqueta textual");
assert.match(categoryBadge, /category\?\.color/, "El color configurado debe actuar como apoyo visual de la categoria");
assert.match(spending, /<CategoryIcon category=\{visual\}/, "El gasto por categoria debe reutilizar la misma iconografia que Movimientos");
assert.match(spending, /getCategoryAccent\(visual\)/, "El gasto por categoria debe resolver el color desde el catalogo visual comun");
assert.match(spending, /progress-fill[^>]*background:\s*accent/, "Cada barra de gasto debe usar el color coherente de su categoria");
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
assert.match(spending, /CATEGORY_CHART_COLORS/, "La evolucion mensual debe reutilizar la familia cromatica de categorias");
assert.doesNotMatch(spending, /useFinancialChartColors/, "La evolucion mensual no debe conservar una paleta financiera paralela");
assert.doesNotMatch(spending, /useChartPalette/, "La grafica de gastos no debe heredar la paleta verde y azul generica");
assert.match(categoryBadge, /CATEGORY_CHART_COLORS[\s\S]*salario[\s\S]*salud[\s\S]*ahorros/, "La evolucion mensual debe derivar sus tres series del catalogo visual comun");
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
