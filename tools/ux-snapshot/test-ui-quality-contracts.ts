import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname, "../..");
const source = (path: string) => readFile(resolve(root, path), "utf8");

const [main, app, settings, layout, markets, transactions, accounts, spending, dashboard, investments, startupExperience, styles, sharedUi, insights, planning, budgetTab, mockData, personalEconomy, quoteRow] = await Promise.all([
  source("apps/desktop/src/main.tsx"),
  source("apps/desktop/src/App.tsx"),
  source("apps/desktop/src/features/settings/SettingsPage.tsx"),
  source("apps/desktop/src/app/layout/RootLayout.tsx"),
  source("apps/desktop/src/features/markets/MarketsPage.tsx"),
  source("apps/desktop/src/features/transactions/TransactionsPage.tsx"),
  source("apps/desktop/src/features/accounts/AccountsPage.tsx"),
  source("apps/desktop/src/features/spending/SpendingPage.tsx"),
  source("apps/desktop/src/features/dashboard/DashboardPage.tsx"),
  source("apps/desktop/src/features/investments/InvestmentsPage.tsx"),
  source("apps/desktop/src/app/StartupExperience.tsx"),
  source("apps/desktop/src/index.css"),
  source("apps/desktop/src/components/ui/Dashboard.tsx"),
  source("apps/desktop/src/features/insights/InsightsPage.tsx"),
  source("apps/desktop/src/pages/PlanificacionPage.tsx"),
  source("apps/desktop/src/features/planning/BudgetTab.tsx"),
  source("apps/desktop/src/lib/api/mock-data.ts"),
  source("apps/desktop/src/features/economy/components/PersonalEconomySection.tsx"),
  source("apps/desktop/src/features/markets/components/QuoteRow.tsx"),
]);

assert.doesNotMatch(layout, /M[aá]s herramientas/, "Objetivos e Insights no deben competir en la navegación lateral.");
assert.doesNotMatch(layout, /to: "\/goals"/, "Objetivos no debe aparecer como acceso de navegación lateral.");
assert.doesNotMatch(layout, /to: "\/insights"/, "Insights no debe aparecer como acceso de navegación lateral.");
assert.match(main, /preloadSettingsOverview\(\)/, "Los datos de Ajustes deben precargarse al iniciar la aplicación.");
assert.match(settings, /loadSettingsOverview\(\)/, "Ajustes debe reutilizar la misma carga precargada.");
assert.doesNotMatch(settings, /if \(loading\)/, "Ajustes no debe bloquear toda la pantalla con un spinner.");
assert.match(markets, /max-w-\[1500px\] mx-auto/, "Mercados debe usar el contenedor centrado compartido.");
assert.match(transactions, /Filtros avanzados/, "Los filtros de movimientos deben poder plegarse.");
assert.match(transactions, /Editar/, "Las acciones de cada movimiento deben tener texto visible.");
assert.match(accounts, /Saldos que requieren revision/, "Las cuentas desactualizadas deben destacarse.");
assert.match(spending, /Comparativa con el mes anterior/, "Gastos debe comparar con el periodo anterior.");
assert.match(spending, /Categoria fuera de lo normal/, "Gastos debe señalar categorías anormales.");
assert.match(dashboard, /Señales del mes/, "El resumen debe priorizar las señales del mes.");
assert.match(investments, /Riesgo de concentracion/, "Inversiones debe mostrar concentración de cartera.");
assert.match(investments, /navigate\("\/markets"/, "La cartera debe enlazar con Mercados.");
assert.match(app, /StartupExperience/, "La aplicación debe incluir una bienvenida breve en cada arranque.");
assert.match(startupExperience, /app-launch-stage/, "La bienvenida debe tener una escena visual de arranque propia.");
assert.match(startupExperience, /onAnimationEnd/, "La bienvenida debe retirarse al terminar su secuencia.");
assert.match(styles, /app-launch-card/, "La bienvenida debe tener una composicion de marca visible, no un spinner.");
assert.match(styles, /prefers-reduced-motion: reduce/, "La bienvenida debe respetar reducir movimiento.");
assert.doesNotMatch(layout, /Centro de control privado/, "El encabezado global no debe mostrar texto redundante.");
assert.doesNotMatch(dashboard, /Centro de control privado/, "El Resumen no debe repetir el texto redundante.");
assert.match(dashboard, /Revisar cuentas/, "Las señales del Resumen deben ofrecer una acción concreta.");
assert.doesNotMatch(dashboard, /bg-primary\/10 p-5/, "Patrimonio neto debe usar la misma superficie que las demás señales.");
assert.match(dashboard, /SectionCard title="Objetivos"/, "Objetivos debe volver a estar disponible desde el Resumen.");
assert.match(dashboard, /SectionCard title="Insights"/, "Insights debe volver a estar disponible desde el Resumen.");
assert.doesNotMatch(dashboard, /className="hidden"/, "Los accesos del Dashboard no deben quedar ocultos.");
assert.match(styles, /--positive:\s*#2F8F6B/, "La aplicación debe usar el verde estandarizado.");
assert.match(styles, /--negative:\s*#C95B66/, "La aplicación debe usar el rojo estandarizado.");
assert.match(styles, /--primary:\s*#5B7EA3/, "El azul debe compartir la misma intensidad moderada que la paleta funcional.");
assert.match(styles, /--warning:\s*#C28A4A/, "El naranja debe compartir la misma intensidad moderada que la paleta funcional.");
assert.doesNotMatch(styles, /--positive:\s*#008163/, "La paleta anterior no debe reaparecer.");
assert.doesNotMatch(styles, /--negative:\s*#ee2526/, "La paleta anterior no debe reaparecer.");
assert.doesNotMatch(styles, /--primary:\s*#0071e3/, "El azul electrico anterior no debe reaparecer.");
assert.doesNotMatch(styles, /--accent:\s*#f56900/, "El naranja electrico anterior no debe reaparecer.");
assert.match(dashboard, /DashboardSkeleton/, "El Resumen debe mantener una estructura visible mientras se cargan datos.");
assert.doesNotMatch(dashboard, /return <LoadingState label="Cargando tu resumen"/, "El arranque no debe degradarse a un spinner de pantalla completa.");
assert.match(sharedUi, /md:text-\[64px\]/, "Las cabeceras deben ser mÃ¡s compactas en escritorio.");
assert.match(accounts, /formatCompactCurrency/, "Las mÃ©tricas de cuentas no deben truncar importes arbitrariamente.");
assert.match(insights, /datos suficientes para analizar/, "Insights debe explicar cÃ³mo resolver la falta de datos.");
assert.match(planning, /BudgetTab/, "PlanificaciÃ³n debe mantener su contenido encapsulado por pestaÃ±as.");
assert.match(budgetTab, /Preparando la planificaciÃ³n/, "PlanificaciÃ³n debe mostrar un estado neutro durante la carga.");
assert.match(mockData, /clean === "\/api\/budgets\/comparison"/, "El entorno demo debe servir comparativas de presupuesto.");
assert.match(styles, /--bg-app:\s*#EFEEEB/, "El tema claro debe partir de un gris cÃ¡lido, no de blanco puro.");
assert.match(settings, /#EFEEEB/, "La muestra del tema claro debe reflejar el fondo gris cÃ¡lido real.");
assert.doesNotMatch(personalEconomy, /<FiscalCalendar\b/, "El calendario fiscal no debe volver a mostrarse en EconomÃ­a.");
assert.match(quoteRow, /Sparkline\(\{ points, positive \}/, "La minigrÃ¡fica debe recibir el signo real de la variaciÃ³n.");
assert.match(quoteRow, /<Sparkline points=\{sparkline\} positive=\{positive\}/, "Las minigrÃ¡ficas negativas deben usar rojo granate.");

console.log("UI quality contracts passed.");
