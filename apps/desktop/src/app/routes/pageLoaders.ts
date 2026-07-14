type PageLoader = () => Promise<unknown>;

export const loadDashboardPage = () => import("@/features/dashboard/DashboardPage");
export const loadFinancesPage = () => import("@/features/finances/FinancesPage");
export const loadInvestmentsPage = () => import("@/features/investments/InvestmentsPage");
export const loadEconomyPage = () => import("@/features/economy/EconomyPage");
export const loadMarketsPage = () => import("@/features/markets/MarketsPage");
export const loadAssistantPage = () => import("@/features/assistant/AssistantPage");
export const loadGoalsPage = () => import("@/features/goals/GoalsPage");
export const loadInsightsPage = () => import("@/features/insights/InsightsPage");
export const loadPositionTrackingPage = () => import("@/features/investments/tracking/PositionTrackingPage");
export const loadPortfolioImportPage = () => import("@/features/investments/import/PortfolioImportPage");
export const loadInstrumentDetailPage = () => import("@/features/markets/detail/InstrumentDetailPage");

const routeLoaders: ReadonlyArray<readonly [string, PageLoader]> = [
  ["/finances", loadFinancesPage],
  ["/investments", loadInvestmentsPage],
  ["/economy", loadEconomyPage],
  ["/markets", loadMarketsPage],
  ["/assistant", loadAssistantPage],
  ["/goals", loadGoalsPage],
  ["/insights", loadInsightsPage],
  ["/", loadDashboardPage],
];

export function preloadRoute(pathname: string): void {
  const loader = routeLoaders.find(([prefix]) => prefix === "/" ? pathname === "/" : pathname.startsWith(prefix))?.[1];
  if (loader) void loader();
}

type IdleWindow = Window & {
  requestIdleCallback?: (callback: () => void, options?: { timeout?: number }) => number;
  cancelIdleCallback?: (id: number) => void;
};

export function warmCoreRoutes(): () => void {
  const coreLoaders = [loadFinancesPage, loadInvestmentsPage, loadEconomyPage, loadMarketsPage];
  const warm = () => { void Promise.allSettled(coreLoaders.map((load) => load())); };
  const idleWindow = window as IdleWindow;

  if (idleWindow.requestIdleCallback) {
    const id = idleWindow.requestIdleCallback(warm, { timeout: 1200 });
    return () => idleWindow.cancelIdleCallback?.(id);
  }

  const id = window.setTimeout(warm, 250);
  return () => window.clearTimeout(id);
}
