import type { Account, Category, Transaction, DashboardOverview, HoldingEnriched, InvestmentAsset, InvestmentSummary, MarketQuote } from "@/lib/types";
import type { SpendingData, CategorySpending } from "./dashboard";
import type { AppSetting } from "./settings";

const mockAccounts: Account[] = [
  {
    id: "mock-acc-1",
    name: "BBVA Cuenta Corriente",
    type: "bank",
    institution: "BBVA",
    currency: "EUR",
    current_balance: "12450.00",
    is_active: true,
    created_at: "2024-01-01T00:00:00",
    updated_at: "2024-01-01T00:00:00",
  },
  {
    id: "mock-acc-2",
    name: "Cartera MyInvestor",
    type: "broker",
    institution: "MyInvestor",
    currency: "EUR",
    current_balance: "28900.00",
    is_active: true,
    created_at: "2024-01-01T00:00:00",
    updated_at: "2024-01-01T00:00:00",
  },
  {
    id: "mock-acc-3",
    name: "Efectivo",
    type: "cash",
    institution: null,
    currency: "EUR",
    current_balance: "350.00",
    is_active: true,
    created_at: "2024-01-01T00:00:00",
    updated_at: "2024-01-01T00:00:00",
  },
  {
    id: "mock-acc-tr",
    name: "Trade Republic",
    type: "broker",
    institution: "Trade Republic",
    currency: "EUR",
    current_balance: "3515.61",
    is_active: true,
    created_at: "2024-01-01T00:00:00",
    updated_at: "2026-06-23T10:00:00",
  },
  {
    id: "mock-acc-finizens",
    name: "Finizens Plan USA",
    type: "investment",
    institution: "Finizens",
    currency: "EUR",
    current_balance: "5569.69",
    is_active: true,
    created_at: "2024-01-01T00:00:00",
    updated_at: "2026-06-23T10:00:00",
  },
  {
    id: "mock-acc-tr-savings",
    name: "Cuenta Remunerada TR",
    type: "savings",
    institution: "Trade Republic",
    currency: "EUR",
    current_balance: "5000.00",
    is_active: true,
    created_at: "2025-01-01T00:00:00",
    updated_at: "2026-06-23T10:00:00",
  },
];

const mockCategories: Category[] = [
  { id: "cat-1", name: "Alimentación", parent_id: null, type: "expense", icon: null, color: "#ec7e00", is_system: true, created_at: "2024-01-01T00:00:00", updated_at: "2024-01-01T00:00:00" },
  { id: "cat-2", name: "Transporte", parent_id: null, type: "expense", icon: null, color: "#494fdf", is_system: true, created_at: "2024-01-01T00:00:00", updated_at: "2024-01-01T00:00:00" },
  { id: "cat-3", name: "Ocio", parent_id: null, type: "expense", icon: null, color: "#00a87e", is_system: true, created_at: "2024-01-01T00:00:00", updated_at: "2024-01-01T00:00:00" },
  { id: "cat-4", name: "Casa", parent_id: null, type: "expense", icon: null, color: "#e23b4a", is_system: true, created_at: "2024-01-01T00:00:00", updated_at: "2024-01-01T00:00:00" },
  { id: "cat-5", name: "Salario", parent_id: null, type: "income", icon: null, color: "#4f55f1", is_system: true, created_at: "2024-01-01T00:00:00", updated_at: "2024-01-01T00:00:00" },
];

const mockTransactions: Transaction[] = [
  { id: "tx-1", account_id: "mock-acc-1", category_id: "cat-1", date: "2026-06-20", description: "Mercadona", amount: "-87.40", currency: "EUR", converted_amount: null, converted_currency: null, type: "expense", source: "manual", source_name: null, external_id: null, import_batch_id: null, notes: null, created_at: "2026-06-20T10:00:00", updated_at: "2026-06-20T10:00:00" },
  { id: "tx-2", account_id: "mock-acc-1", category_id: "cat-2", date: "2026-06-19", description: "Renfe AVE Madrid", amount: "-42.50", currency: "EUR", converted_amount: null, converted_currency: null, type: "expense", source: "manual", source_name: null, external_id: null, import_batch_id: null, notes: null, created_at: "2026-06-19T10:00:00", updated_at: "2026-06-19T10:00:00" },
  { id: "tx-3", account_id: "mock-acc-1", category_id: "cat-3", date: "2026-06-18", description: "Netflix", amount: "-15.99", currency: "EUR", converted_amount: null, converted_currency: null, type: "expense", source: "manual", source_name: null, external_id: null, import_batch_id: null, notes: null, created_at: "2026-06-18T10:00:00", updated_at: "2026-06-18T10:00:00" },
  { id: "tx-4", account_id: "mock-acc-1", category_id: "cat-4", date: "2026-06-15", description: "Alquiler junio", amount: "-950.00", currency: "EUR", converted_amount: null, converted_currency: null, type: "expense", source: "manual", source_name: null, external_id: null, import_batch_id: null, notes: null, created_at: "2026-06-15T10:00:00", updated_at: "2026-06-15T10:00:00" },
  { id: "tx-5", account_id: "mock-acc-1", category_id: "cat-5", date: "2026-06-01", description: "Nómina junio", amount: "2800.00", currency: "EUR", converted_amount: null, converted_currency: null, type: "income", source: "manual", source_name: null, external_id: null, import_batch_id: null, notes: null, created_at: "2026-06-01T10:00:00", updated_at: "2026-06-01T10:00:00" },
];

const mockOverview: DashboardOverview = {
  net_worth: "41700.00",
  liquidity: "12800.00",
  investments: "28900.00",
  monthly_income: "2800.00",
  monthly_expense: "1095.89",
  monthly_savings: "1704.11",
  savings_rate: 0.608,
  currency: "EUR",
};

const mockSpendingCategories: CategorySpending[] = [
  { category_id: "cat-4", category: "Casa", amount: "950.00", percentage: 86.7 },
  { category_id: "cat-1", category: "Alimentación", amount: "87.40", percentage: 8.0 },
  { category_id: "cat-2", category: "Transporte", amount: "42.50", percentage: 3.9 },
  { category_id: "cat-3", category: "Ocio", amount: "15.99", percentage: 1.4 },
];

const mockSpending: SpendingData = {
  month: "2026-06",
  period_type: "month",
  total_expense: "1095.89",
  total_income: "2800.00",
  net_savings: "1704.11",
  savings_rate: 60.8,
  transaction_count: 5,
  average_daily_expense: "36.53",
  by_category: mockSpendingCategories,
};

const mockInvestmentAssets: InvestmentAsset[] = [
  {
    id: "asset-tr-savings", name: "Cuenta Remunerada Trade Republic", ticker: null, isin: null,
    asset_type: "savings_account", currency: "EUR", region: null, sector: null,
    price_source: "manual", created_at: "2024-01-01T00:00:00", updated_at: "2026-06-23T10:00:00",
  },
];

const assetMap = Object.fromEntries(mockInvestmentAssets.map(a => [a.id, a]));

const mockHoldings: HoldingEnriched[] = [
  {
    id: "h-savings", account_id: "mock-acc-tr-savings", asset_id: "asset-tr-savings",
    quantity: "5000.00000000", average_price: "1.0000", current_price: null,
    current_price_currency: "EUR", current_price_updated_at: null,
    market_value: "5000.00", interest_rate: "0.0400", inception_date: "2025-01-01",
    created_at: "2025-01-01T00:00:00", updated_at: "2026-06-23T10:00:00",
    asset: assetMap["asset-tr-savings"],
    cost_basis: "5000.00000000", return_absolute: null, return_percent: null, accrued_interest: "72.33",
    display_name: "Cuenta Remunerada Trade Republic", symbol: null, asset_type: "cash", broker: "mock-acc-tr-savings",
    invested_amount: "5000.00", unrealized_pnl: "0.00", unrealized_pnl_pct: 0, currency: "EUR",
    is_mock: false, quality_score: 0.8, warnings: ["Precio actual no disponible; puede editarse manualmente."],
  },
];

const mockInvestmentSummary: InvestmentSummary = {
  total_value: "5000.00",
  total_invested: "5000.00",
  return_absolute: "0.00",
  return_percent: 0,
  currency: "EUR",
  by_account: [{ account_id: "mock-acc-tr-savings", value: "5000.00", invested: "5000.00" }],
  last_updated: null,
};

const mockSettings: AppSetting[] = [
  { id: "set-1", key: "app.language", value_json: '"es"', created_at: "2024-01-01T00:00:00", updated_at: "2024-01-01T00:00:00" },
  { id: "set-2", key: "theme.mode", value_json: '"dark"', created_at: "2024-01-01T00:00:00", updated_at: "2024-01-01T00:00:00" },
  { id: "set-3", key: "app.currency", value_json: '"EUR"', created_at: "2024-01-01T00:00:00", updated_at: "2024-01-01T00:00:00" },
];

const mockGoals: import("./goals").Goal[] = [];

// Sparkline sintético: tendencia con ruido
function makeSparkline(base: number, trend: number): number[] {
  return Array.from({ length: 20 }, (_, i) => {
    const noise = (Math.sin(i * 1.3) + Math.cos(i * 0.7)) * base * 0.003;
    return parseFloat((base + trend * i * 0.1 + noise).toFixed(4));
  });
}

const rawMockMarketQuotes: Array<
  Omit<
    MarketQuote,
    | "change_absolute"
    | "freshness_status"
    | "source"
    | "is_fallback"
    | "is_stale"
    | "warning"
    | "confidence_score"
  >
> = [
  // Europa
  { symbol: "^IBEX", name: "IBEX 35", category: "indices_eu", price: 12843.50, change_pct: 0.73, currency: "EUR", sparkline: makeSparkline(12750, 9.3), last_updated: "2026-06-23T10:00:00Z", market_open: true },
  { symbol: "^STOXX50E", name: "Euro Stoxx 50", category: "indices_eu", price: 5312.80, change_pct: 0.45, currency: "EUR", sparkline: makeSparkline(5289, 2.4), last_updated: "2026-06-23T10:00:00Z", market_open: true },
  { symbol: "^STOXX", name: "STOXX Europe 600", category: "indices_eu", price: 546.20, change_pct: 0.38, currency: "EUR", sparkline: makeSparkline(544, 0.2), last_updated: "2026-06-23T10:00:00Z", market_open: true },
  { symbol: "^GDAXI", name: "DAX", category: "indices_eu", price: 23156.40, change_pct: 0.52, currency: "EUR", sparkline: makeSparkline(23036, 12.0), last_updated: "2026-06-23T10:00:00Z", market_open: true },
  { symbol: "^FCHI", name: "CAC 40", category: "indices_eu", price: 7834.60, change_pct: 0.31, currency: "EUR", sparkline: makeSparkline(7810, 2.5), last_updated: "2026-06-23T10:00:00Z", market_open: true },
  { symbol: "^FTSE", name: "FTSE 100", category: "indices_eu", price: 8642.30, change_pct: -0.12, currency: "GBP", sparkline: makeSparkline(8660, -1.8), last_updated: "2026-06-23T10:00:00Z", market_open: true },
  // EEUU
  { symbol: "^GSPC", name: "S&P 500", category: "indices_us", price: 5945.28, change_pct: 1.12, currency: "USD", sparkline: makeSparkline(5879, 6.6), last_updated: "2026-06-23T10:00:00Z", market_open: true },
  { symbol: "^NDX", name: "Nasdaq 100", category: "indices_us", price: 21432.60, change_pct: 1.38, currency: "USD", sparkline: makeSparkline(21138, 29.4), last_updated: "2026-06-23T10:00:00Z", market_open: true },
  { symbol: "^DJI", name: "Dow Jones", category: "indices_us", price: 43128.40, change_pct: 0.67, currency: "USD", sparkline: makeSparkline(42841, 28.7), last_updated: "2026-06-23T10:00:00Z", market_open: true },
  { symbol: "^RUT", name: "Russell 2000", category: "indices_us", price: 2184.75, change_pct: 0.94, currency: "USD", sparkline: makeSparkline(2164, 2.1), last_updated: "2026-06-23T10:00:00Z", market_open: true },
  // Asia
  { symbol: "^N225", name: "Nikkei 225", category: "indices_asia", price: 38420.50, change_pct: -0.45, currency: "JPY", sparkline: makeSparkline(38595, -17.5), last_updated: "2026-06-23T06:00:00Z", market_open: false },
  { symbol: "^HSI", name: "Hang Seng", category: "indices_asia", price: 23145.80, change_pct: 0.82, currency: "HKD", sparkline: makeSparkline(22957, 18.9), last_updated: "2026-06-23T08:00:00Z", market_open: false },
  { symbol: "000001.SS", name: "Shanghai Composite", category: "indices_asia", price: 3421.60, change_pct: 0.23, currency: "CNY", sparkline: makeSparkline(3413, 0.8), last_updated: "2026-06-23T07:30:00Z", market_open: false },
  { symbol: "^NSEI", name: "Nifty 50", category: "indices_asia", price: 24856.30, change_pct: 0.61, currency: "INR", sparkline: makeSparkline(24704, 15.2), last_updated: "2026-06-23T09:00:00Z", market_open: false },
  // Cripto
  { symbol: "BTC-USD", name: "Bitcoin", category: "crypto", price: 107234.50, change_pct: 2.14, currency: "USD", sparkline: makeSparkline(104980, 225.4), last_updated: "2026-06-23T10:00:00Z", market_open: true },
  { symbol: "ETH-USD", name: "Ethereum", category: "crypto", price: 3842.60, change_pct: 1.87, currency: "USD", sparkline: makeSparkline(3771, 7.2), last_updated: "2026-06-23T10:00:00Z", market_open: true },
  { symbol: "BNB-USD", name: "BNB", category: "crypto", price: 712.40, change_pct: 0.93, currency: "USD", sparkline: makeSparkline(705, 0.7), last_updated: "2026-06-23T10:00:00Z", market_open: true },
  { symbol: "SOL-USD", name: "Solana", category: "crypto", price: 186.35, change_pct: 3.21, currency: "USD", sparkline: makeSparkline(180, 0.6), last_updated: "2026-06-23T10:00:00Z", market_open: true },
  // Divisas
  { symbol: "EURUSD=X", name: "EUR/USD", category: "fx", price: 1.1342, change_pct: 0.18, currency: "USD", sparkline: makeSparkline(1.1322, 0.001), last_updated: "2026-06-23T10:00:00Z", market_open: true },
  { symbol: "EURGBP=X", name: "EUR/GBP", category: "fx", price: 0.8423, change_pct: -0.09, currency: "GBP", sparkline: makeSparkline(0.8431, -0.0001), last_updated: "2026-06-23T10:00:00Z", market_open: true },
  { symbol: "EURJPY=X", name: "EUR/JPY", category: "fx", price: 163.48, change_pct: 0.32, currency: "JPY", sparkline: makeSparkline(162.96, 0.052), last_updated: "2026-06-23T10:00:00Z", market_open: true },
  { symbol: "GBPUSD=X", name: "GBP/USD", category: "fx", price: 1.3467, change_pct: 0.27, currency: "USD", sparkline: makeSparkline(1.3431, 0.0036), last_updated: "2026-06-23T10:00:00Z", market_open: true },
  { symbol: "JPY=X", name: "USD/JPY", category: "fx", price: 144.12, change_pct: -0.14, currency: "JPY", sparkline: makeSparkline(144.32, -0.02), last_updated: "2026-06-23T10:00:00Z", market_open: true },
  { symbol: "CHF=X", name: "USD/CHF", category: "fx", price: 0.8934, change_pct: -0.21, currency: "CHF", sparkline: makeSparkline(0.8953, -0.0002), last_updated: "2026-06-23T10:00:00Z", market_open: true },
  // Bonos 10Y
  { symbol: "^TNX", name: "Treasury EEUU 10Y", category: "bonds", price: 4.32, change_pct: -0.46, currency: "USD", sparkline: makeSparkline(4.34, -0.002), last_updated: "2026-06-23T10:00:00Z", market_open: false },
  { symbol: "^TMBMKDE-10Y", name: "Bund Alemania 10Y", category: "bonds", price: 2.56, change_pct: -0.78, currency: "EUR", sparkline: makeSparkline(2.58, -0.002), last_updated: "2026-06-23T10:00:00Z", market_open: true },
  { symbol: "^TMBMKES-10Y", name: "Bono España 10Y", category: "bonds", price: 3.12, change_pct: -0.63, currency: "EUR", sparkline: makeSparkline(3.14, -0.002), last_updated: "2026-06-23T10:00:00Z", market_open: true },
  { symbol: "^TMBMKGB-10Y", name: "Gilt UK 10Y", category: "bonds", price: 4.68, change_pct: -0.21, currency: "GBP", sparkline: makeSparkline(4.69, -0.001), last_updated: "2026-06-23T10:00:00Z", market_open: true },
  { symbol: "^TMBMKIT-10Y", name: "BTP Italia 10Y", category: "bonds", price: 3.87, change_pct: -0.51, currency: "EUR", sparkline: makeSparkline(3.89, -0.002), last_updated: "2026-06-23T10:00:00Z", market_open: true },
  // Materias primas
  { symbol: "GC=F", name: "Oro", category: "commodities", price: 3324.80, change_pct: 0.54, currency: "USD", sparkline: makeSparkline(3307, 1.8), last_updated: "2026-06-23T10:00:00Z", market_open: true },
  { symbol: "SI=F", name: "Plata", category: "commodities", price: 36.42, change_pct: 0.88, currency: "USD", sparkline: makeSparkline(36.10, 0.032), last_updated: "2026-06-23T10:00:00Z", market_open: true },
  { symbol: "BZ=F", name: "Petróleo Brent", category: "commodities", price: 84.32, change_pct: -0.71, currency: "USD", sparkline: makeSparkline(84.92, -0.06), last_updated: "2026-06-23T10:00:00Z", market_open: true },
  { symbol: "CL=F", name: "Petróleo WTI", category: "commodities", price: 81.15, change_pct: -0.83, currency: "USD", sparkline: makeSparkline(81.83, -0.068), last_updated: "2026-06-23T10:00:00Z", market_open: true },
  { symbol: "NG=F", name: "Gas Natural", category: "commodities", price: 2.847, change_pct: 1.43, currency: "USD", sparkline: makeSparkline(2.807, 0.004), last_updated: "2026-06-23T10:00:00Z", market_open: true },
  { symbol: "HG=F", name: "Cobre", category: "commodities", price: 4.732, change_pct: 0.66, currency: "USD", sparkline: makeSparkline(4.701, 0.0031), last_updated: "2026-06-23T10:00:00Z", market_open: true },
  // Volatilidad
  { symbol: "^VIX", name: "VIX", category: "volatility", price: 14.82, change_pct: -3.44, currency: "USD", sparkline: makeSparkline(15.35, -0.053), last_updated: "2026-06-23T10:00:00Z", market_open: false },
];

export const mockMarketQuotes: MarketQuote[] = rawMockMarketQuotes.map((quote) => ({
  ...quote,
  change_absolute: null,
  freshness_status: "delayed",
  source: "mock",
  is_fallback: false,
  is_stale: false,
  warning: null,
  confidence_score: 1,
}));

export function getMockResponse<T>(path: string, init?: RequestInit): T {
  const clean = path.split("?")[0];

  if (clean === "/api/accounts") return mockAccounts as T;
  if (clean === "/api/categories") return mockCategories as T;
  if (clean === "/api/transactions") return mockTransactions as T;
  if (clean === "/api/dashboard/overview") return mockOverview as T;
  if (clean === "/api/dashboard/spending/years") return { years: [2026] } as T;
  if (clean === "/api/dashboard/spending") return mockSpending as T;
  if (clean === "/api/settings") return mockSettings as T;
  if (clean.startsWith("/api/settings/")) {
    const key = decodeURIComponent(clean.slice("/api/settings/".length));
    const existing = mockSettings.find((setting) => setting.key === key);
    const payload = typeof init?.body === "string" ? JSON.parse(init.body) as { value_json?: string } : {};
    const updated = existing ?? {
      id: `mock-${key}`,
      key,
      value_json: '""',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    if (payload.value_json !== undefined) updated.value_json = payload.value_json;
    updated.updated_at = new Date().toISOString();
    return updated as T;
  }
  if (clean === "/api/goals") {
    if (init?.method === "POST" && typeof init.body === "string") {
      const payload = JSON.parse(init.body) as import("./goals").GoalCreate;
      const now = new Date().toISOString();
      const goal: import("./goals").Goal = { ...payload, id: crypto.randomUUID(), status: "active", created_at: now, updated_at: now };
      mockGoals.unshift(goal);
      return goal as T;
    }
    return [...mockGoals] as T;
  }
  if (clean.startsWith("/api/goals/")) {
    const id = clean.slice("/api/goals/".length);
    const index = mockGoals.findIndex((goal) => goal.id === id);
    if (init?.method === "DELETE") { if (index >= 0) mockGoals.splice(index, 1); return undefined as T; }
    if (init?.method === "PATCH" && index >= 0 && typeof init.body === "string") {
      mockGoals[index] = { ...mockGoals[index], ...JSON.parse(init.body), updated_at: new Date().toISOString() };
      return mockGoals[index] as T;
    }
  }
  if (clean.startsWith("/api/accounts/") && init?.method === "DELETE") return undefined as T;
  if (clean === "/api/investments/assets") return mockInvestmentAssets as T;
  if (clean === "/api/investments/holdings") return mockHoldings as T;
  if (clean === "/api/investments/summary") return mockInvestmentSummary as T;
  if (clean === "/api/investments/prices/refresh")
    return { ok: true, updated: 0, failed: [], needs_manual_nav: [], updated_items: [], manual_required: [], skipped: [], errors: [] } as T;
  if (path.startsWith("/api/markets/quotes")) {
    const catParam = path.includes("?category=")
      ? path.split("?category=")[1]
      : null;
    const quotes = catParam
      ? mockMarketQuotes.filter((q) => q.category === catParam)
      : mockMarketQuotes;
    return quotes as unknown as T;
  }

  throw new Error(`[mock] No mock defined for: ${path}`);
}
