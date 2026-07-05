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
  { id: "tx-1", account_id: "mock-acc-1", account_name: "Cuenta demo", category_id: "cat-1", date: "2026-06-20", description: "Mercadona", amount: "-87.40", currency: "EUR", converted_amount: null, converted_currency: null, type: "expense", source: "manual", source_name: null, external_id: null, import_batch_id: null, analytics_scope: "personal" as const, linked_transaction_id: null, notes: null, created_at: "2026-06-20T10:00:00", updated_at: "2026-06-20T10:00:00" },
  { id: "tx-2", account_id: "mock-acc-1", account_name: "Cuenta demo", category_id: "cat-2", date: "2026-06-19", description: "Renfe AVE Madrid", amount: "-42.50", currency: "EUR", converted_amount: null, converted_currency: null, type: "expense", source: "manual", source_name: null, external_id: null, import_batch_id: null, analytics_scope: "personal" as const, linked_transaction_id: null, notes: null, created_at: "2026-06-19T10:00:00", updated_at: "2026-06-19T10:00:00" },
  { id: "tx-3", account_id: "mock-acc-1", account_name: "Cuenta demo", category_id: "cat-3", date: "2026-06-18", description: "Netflix", amount: "-15.99", currency: "EUR", converted_amount: null, converted_currency: null, type: "expense", source: "manual", source_name: null, external_id: null, import_batch_id: null, analytics_scope: "personal" as const, linked_transaction_id: null, notes: null, created_at: "2026-06-18T10:00:00", updated_at: "2026-06-18T10:00:00" },
  { id: "tx-4", account_id: "mock-acc-1", account_name: "Cuenta demo", category_id: "cat-4", date: "2026-06-15", description: "Alquiler junio", amount: "-950.00", currency: "EUR", converted_amount: null, converted_currency: null, type: "expense", source: "manual", source_name: null, external_id: null, import_batch_id: null, analytics_scope: "personal" as const, linked_transaction_id: null, notes: null, created_at: "2026-06-15T10:00:00", updated_at: "2026-06-15T10:00:00" },
  { id: "tx-5", account_id: "mock-acc-1", account_name: "Cuenta demo", category_id: "cat-5", date: "2026-06-01", description: "Nómina junio", amount: "2800.00", currency: "EUR", converted_amount: null, converted_currency: null, type: "income", source: "manual", source_name: null, external_id: null, import_batch_id: null, analytics_scope: "personal" as const, linked_transaction_id: null, notes: null, created_at: "2026-06-01T10:00:00", updated_at: "2026-06-01T10:00:00" },
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
  pending_valuation_count: 0,
  pending_valuation_invested: "0.00",
};

const mockReconciliation: import("./investments").ReconciliationReport = {
  generated_at: "2026-06-30T07:15:00Z",
  portfolio_value_eur: 5000,
  completeness: {
    confirmed_pct: 68,
    estimated_pct: 18,
    manual_pct: 10,
    no_price_pct: 4,
  },
  holdings: [
    {
      holding_id: "h-savings",
      display_name: "Cuenta Remunerada Trade Republic",
      ticker: null,
      quality_state: "manual",
      value_eur: 5000,
      weight_pct: 100,
      unrealized_pnl: 0,
      unrealized_pnl_pct: 0,
      currency: "EUR",
      requires_fx: false,
      broker: "Trade Republic",
      sector: "Cash",
      asset_type: "savings_account",
    },
  ],
  weights_by: {
    currency: [{ key: "EUR", weight_pct: 100 }],
    sector: [{ key: "Cash", weight_pct: 100 }],
    broker: [{ key: "Trade Republic", weight_pct: 100 }],
    asset_type: [{ key: "savings_account", weight_pct: 100 }],
    region: [{ key: "Europa", weight_pct: 100 }],
  },
  concentration_alerts: [{ type: "asset", key: "Cuenta Remunerada Trade Republic", weight_pct: 100, threshold_pct: 35 }],
};

const mockSettings: AppSetting[] = [
  { id: "set-1", key: "app.language", value_json: '"es"', created_at: "2024-01-01T00:00:00", updated_at: "2024-01-01T00:00:00" },
  { id: "set-2", key: "theme.mode", value_json: '"dark"', created_at: "2024-01-01T00:00:00", updated_at: "2024-01-01T00:00:00" },
  { id: "set-3", key: "app.currency", value_json: '"EUR"', created_at: "2024-01-01T00:00:00", updated_at: "2024-01-01T00:00:00" },
];

const mockBackups = [
  {
    filename: "financial-20260630-084500.sqlite",
    size_bytes: 245760,
    created_at: "2026-06-30T08:45:00",
  },
];

const mockGoals: import("./goals").Goal[] = [];

const mockRecurring: import("./budgets").RecurringTransaction[] = [
  {
    id: "rec-1",
    name: "Alquiler",
    category_id: "cat-4",
    account_id: "mock-acc-1",
    amount: 950,
    currency: "EUR",
    type: "expense",
    frequency: "monthly",
    day_of_month: 1,
    day_of_week: null,
    month_of_year: null,
    next_date: "2026-07-01",
    active: true,
    description: "Pago mensual de vivienda",
    created_at: "2026-06-01T08:00:00",
    updated_at: "2026-06-01T08:00:00",
  },
];

const mockRecurringCandidates: import("./budgets").RecurringCandidate[] = [
  {
    id: "cand-netflix",
    name: "Netflix",
    description: "Cargo mensual detectado con importe estable.",
    amount: 15.99,
    amount_min: 15.99,
    amount_max: 15.99,
    currency: "EUR",
    type: "expense",
    frequency: "monthly",
    next_date: "2026-07-18",
    confidence: 0.92,
    transaction_count: 3,
    transaction_ids: ["tx-3"],
    category_id: "cat-3",
    account_id: "mock-acc-1",
    evidence: ["18/04 Netflix 15,99 EUR", "18/05 Netflix 15,99 EUR", "18/06 Netflix 15,99 EUR"],
  },
];

const mockCalendar: import("./budgets").CalendarEvent[] = [
  { recurring_id: "rec-1", name: "Alquiler", amount: 950, type: "expense", date: "2026-07-01", category_name: "Casa" },
];

const mockHouseholdBills: import("./household-bills").HouseholdBill[] = [
  {
    id: "bill-1",
    provider: "Iberdrola",
    service_type: "electricity",
    period_start: "2026-05-01",
    period_end: "2026-05-31",
    amount: "71.20",
    currency: "EUR",
    category_id: "cat-4",
    is_recurring: true,
    due_date: "2026-06-05",
    paid_at: "2026-06-05T09:00:00",
    notes: null,
    created_at: "2026-06-05T09:00:00",
    updated_at: "2026-06-05T09:00:00",
  },
  {
    id: "bill-2",
    provider: "Movistar",
    service_type: "internet",
    period_start: "2026-05-01",
    period_end: "2026-05-31",
    amount: "54.90",
    currency: "EUR",
    category_id: "cat-4",
    is_recurring: true,
    due_date: "2026-06-10",
    paid_at: "2026-06-10T09:00:00",
    notes: null,
    created_at: "2026-06-10T09:00:00",
    updated_at: "2026-06-10T09:00:00",
  },
];

const mockHouseholdSummary: import("./household-bills").HouseholdBillSummary = {
  generated_at: "2026-06-30T07:15:00Z",
  total_monthly_estimate: 126.1,
  items: [
    {
      service_type: "electricity",
      provider: "Iberdrola",
      bills_count: 2,
      last_amount: 71.2,
      previous_amount: 62.4,
      change_pct: 14.1,
      average_amount: 66.8,
      next_estimate: 66.8,
      anomaly: false,
      latest_period: "2026-05",
    },
    {
      service_type: "internet",
      provider: "Movistar",
      bills_count: 1,
      last_amount: 54.9,
      previous_amount: null,
      change_pct: null,
      average_amount: 54.9,
      next_estimate: 54.9,
      anomaly: false,
      latest_period: "2026-05",
    },
  ],
};

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

// ── Market Intelligence (página Economía) ────────────────────────────────────

function macroHistory(latest: number, step: number, months = 13) {
  const points = [];
  for (let i = months - 1; i >= 0; i--) {
    const d = new Date(2026, 5 - i, 1);
    points.push({
      period: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`,
      value: Number((latest - step * i).toFixed(2)),
    });
  }
  return points;
}

function macroPoint(
  id: string,
  name: string,
  value: number,
  unit: string,
  subcategory: string,
  opts: { priority?: string; frequency?: string; step?: number; period?: string; country?: string } = {}
) {
  const history = macroHistory(value, opts.step ?? 0.1);
  return {
    catalog_item_id: id,
    indicator_id: id,
    country: opts.country ?? "ES",
    period: opts.period ?? "2026-06",
    value,
    unit,
    provider_id: "mock",
    quality_score: 0.95,
    data_status: "ok",
    retrieved_at: "2026-07-01T09:00:00Z",
    display_name: name,
    description: name,
    subcategory,
    frequency: opts.frequency ?? "monthly",
    priority: opts.priority ?? "critical",
    previous_value: history[history.length - 2]?.value ?? null,
    delta: Number((value - (history[history.length - 2]?.value ?? value)).toFixed(2)),
    history,
  };
}

const mockMacroSnapshot = {
  status: "ok",
  spain: [
    macroPoint("ipc_general", "IPC General España", 2.8, "%", "inflation", { step: 0.08 }),
    macroPoint("ipc_subyacente", "IPC Subyacente España", 2.4, "%", "inflation", { step: 0.05 }),
    macroPoint("euribor_12m", "Euríbor 12M", 2.17, "%", "interest_rates", { step: -0.04 }),
    macroPoint("tipo_bce", "Tipo BCE", 2.15, "%", "interest_rates", { step: -0.05 }),
    macroPoint("desempleo_spain", "Desempleo España", 10.6, "%", "employment", { step: -0.09 }),
    macroPoint("pib_spain", "PIB España", 1687.15, "EUR bn", "gdp", { frequency: "yearly", period: "2025", step: 12 }),
    macroPoint("confianza_consumidor_spain", "Confianza del Consumidor España", 86, "index", "sentiment", { priority: "medium", step: 0.6 }),
  ],
  eurozone: [
    macroPoint("inflation_eurozone", "Inflación Eurozona", 2.2, "%", "inflation", { country: "EU", step: 0.04 }),
    macroPoint("unemployment_eurozone", "Desempleo Eurozona", 6.3, "%", "employment", { country: "EU", step: -0.02 }),
  ],
  usa: [
    macroPoint("fed_funds_rate", "Fed Funds Rate", 3.63, "%", "interest_rates", { country: "US", step: -0.06 }),
    macroPoint("cpi_usa", "CPI USA", 2.6, "%", "inflation", { country: "US", step: 0.03 }),
    macroPoint("unemployment_usa", "Desempleo USA", 4.3, "%", "employment", { country: "US", step: 0.02 }),
    macroPoint("industrial_production_usa", "Producción Industrial USA", 102.65, "index", "industrial", { country: "US", priority: "high", step: 0.2 }),
    macroPoint("consumer_sentiment_usa", "Consumer Sentiment USA", 61.2, "index", "sentiment", { country: "US", priority: "medium", step: 0.8 }),
  ],
  generated_at: "2026-07-01T09:00:00Z",
  warnings: [],
};

const mockBondSnapshot = {
  yields: [
    { catalog_item_id: "us_2y", country: "US", maturity: "2Y", yield_value: 3.72, date: "2026-06-30", provider_id: "mock", quality_score: 1, data_status: "ok" },
    { catalog_item_id: "us_5y", country: "US", maturity: "5Y", yield_value: 3.85, date: "2026-06-30", provider_id: "mock", quality_score: 1, data_status: "ok" },
    { catalog_item_id: "us_10y", country: "US", maturity: "10Y", yield_value: 4.1, date: "2026-06-30", provider_id: "mock", quality_score: 1, data_status: "ok" },
    { catalog_item_id: "us_30y", country: "US", maturity: "30Y", yield_value: 4.45, date: "2026-06-30", provider_id: "mock", quality_score: 1, data_status: "ok" },
    { catalog_item_id: "spain_10y", country: "ES", maturity: "10Y", yield_value: 3.12, date: "2026-06-30", provider_id: "mock", quality_score: 1, data_status: "ok" },
    { catalog_item_id: "germany_10y", country: "DE", maturity: "10Y", yield_value: 2.56, date: "2026-06-30", provider_id: "mock", quality_score: 1, data_status: "ok" },
  ],
  generated_at: "2026-07-01T09:00:00Z",
  warnings: [],
};

const mockQuote = (catalog_item_id: string, name: string, price: number, change_pct: number, currency = "USD", country = "US") => ({
  catalog_item_id, symbol: catalog_item_id.toUpperCase(), asset_type: "index",
  price, change_pct, currency, observed_at: "2026-06-30T22:00:00Z",
  provider_id: "mock", quality_score: 1, data_status: "ok",
  display_name: name, display_country: country,
});

const mockMarketSnapshot = {
  status: "ok",
  indices: [
    mockQuote("sp500", "S&P 500", 7483.24, 0.42),
    mockQuote("nasdaq", "Nasdaq Composite", 25832.67, -0.8),
    mockQuote("ibex35", "IBEX 35", 19783.8, 0.57, "EUR", "ES"),
    mockQuote("eurostoxx50", "EuroStoxx 50", 6386.23, 0.4, "EUR", "EA"),
  ],
  crypto: [
    mockQuote("bitcoin", "Bitcoin", 61880, 1.13, "USD", "GLOBAL"),
    mockQuote("ethereum", "Ethereum", 1743.14, 6.03, "USD", "GLOBAL"),
  ],
  commodities: [
    mockQuote("gold", "Oro", 4190.3, 1.9, "USD", "GLOBAL"),
    mockQuote("brent", "Brent Crude Oil", 71.4, -0.6, "USD", "GLOBAL"),
  ],
  generated_at: "2026-07-01T09:00:00Z",
  warnings: [],
  quality_score: 1,
};

const mockForexSnapshot = {
  rates: [
    { catalog_item_id: "eur_usd", base_currency: "EUR", quote_currency: "USD", rate: 1.1342, date: "2026-06-30", provider_id: "mock", quality_score: 1, data_status: "ok" },
  ],
  generated_at: "2026-07-01T09:00:00Z",
  warnings: [],
};

const mockPersonalImpact = {
  generated_at: "2026-07-01T09:00:00Z",
  comparatives: [
    {
      id: "real_portfolio_return",
      title: "Rentabilidad real de tu cartera",
      description: "Rentabilidad de tu cartera menos la inflación. Positiva significa que ganas poder adquisitivo.",
      market_value: 2.8, market_label: "IPC (referencia): 2.80%",
      personal_value: -16.07, personal_label: "Rentabilidad real: -16.07%",
      signal: "negative", signal_text: "Tu cartera pierde frente a la inflación",
      source_ids: ["ipc_general"],
    },
    {
      id: "inflation_vs_savings",
      title: "Inflación vs tu tasa de ahorro",
      description: "Tu tasa de ahorro mensual comparada con el IPC general. Por encima de la inflación significa que mantienes poder adquisitivo.",
      market_value: 2.8, market_label: "IPC General: 2.80%",
      personal_value: 22.54, personal_label: "Tu ahorro: 22.54%",
      signal: "positive", signal_text: "Estás por encima de la inflación · La inflación cuesta ~29 €/mes a tu efectivo",
      source_ids: ["ipc_general"],
    },
    {
      id: "rates_vs_liquidity",
      title: "Tipos BCE vs tu liquidez",
      description: "Con tipos altos conviene tener colchón de liquidez. Se recomiendan mínimo 3 meses de gastos cubiertos.",
      market_value: 2.15, market_label: "Tipo BCE: 2.15%",
      personal_value: 7.0, personal_label: "Tu liquidez: 7.0 meses",
      signal: "positive", signal_text: "Tienes colchón suficiente · A tipo BCE tu efectivo podría rentar ~22 €/mes",
      source_ids: ["tipo_bce"],
    },
    {
      id: "purchasing_power",
      title: "Poder adquisitivo actual",
      description: "El IPC general mide la pérdida de poder adquisitivo. Por debajo del 2% es el objetivo del BCE.",
      market_value: 2.8, market_label: "IPC General: 2.80%",
      personal_value: null, personal_label: "Indicador macro",
      signal: "neutral", signal_text: "Inflación moderada (2.80%)",
      source_ids: ["ipc_general"],
    },
    {
      id: "risk_premium_spain",
      title: "Prima de riesgo España",
      description: "Diferencial bono español 10Y vs bund alemán en puntos básicos.",
      market_value: 56, market_label: "Prima de riesgo: 56 bps",
      personal_value: null, personal_label: "Indicador macro",
      signal: "positive", signal_text: "Prima de riesgo controlada",
      source_ids: ["spain_10y", "germany_10y"],
    },
    {
      id: "market_vs_portfolio",
      title: "Mercado vs rentabilidad de tu cartera",
      description: "Variación media de S&P 500, IBEX 35 y EuroStoxx 50 en los últimos 12 meses frente al retorno de tu cartera desde la compra.",
      market_value: null, market_label: "Índices (12 meses): Sin datos",
      personal_value: -13.27, personal_label: "Tu cartera (desde compra): -13.27%",
      signal: "no_data", signal_text: "Sin datos de mercado — comparativa no disponible",
      source_ids: ["sp500", "ibex35", "eurostoxx50"],
    },
    {
      id: "oil_vs_transport",
      title: "Petróleo vs tu gasto en transporte",
      description: "El precio del Brent impacta en los carburantes. Por debajo de 80 USD/barril es favorable.",
      market_value: null, market_label: "Brent: Sin datos",
      personal_value: 19, personal_label: "Transporte/mes: 19 €",
      signal: "no_data", signal_text: "Sin datos de mercado — comparativa no disponible",
      source_ids: ["brent"],
    },
  ],
  warnings: ["2 comparativas sin datos de mercado disponibles."],
};

const mockIngestStatus = {
  status: "done",
  last_run: "2026-07-01T09:00:00Z",
  count: 24,
  results: [],
  storage: "file",
};

export function getMockResponse<T>(path: string, init?: RequestInit): T {
  const clean = path.split("?")[0];

  if (clean === "/api/accounts") return mockAccounts as T;
  if (clean === "/api/categories") return mockCategories as T;
  if (clean === "/api/transactions") return mockTransactions as T;
  if (clean === "/api/dashboard/overview") return mockOverview as T;
  if (clean === "/api/dashboard/spending/years") return { years: [2026] } as T;
  if (clean === "/api/dashboard/spending/monthly") return [
    { month: "2026-02", income: "2650.00", expense: "1420.50", savings: "1229.50" },
    { month: "2026-03", income: "2650.00", expense: "1611.20", savings: "1038.80" },
    { month: "2026-04", income: "2800.00", expense: "1245.75", savings: "1554.25" },
    { month: "2026-05", income: "2800.00", expense: "1780.10", savings: "1019.90" },
    { month: "2026-06", income: "2800.00", expense: "1382.50", savings: "1417.50" },
    { month: "2026-07", income: "2800.00", expense: "1095.89", savings: "1704.11" },
  ] as T;
  if (clean === "/api/dashboard/spending") return mockSpending as T;
  if (clean === "/api/settings") return mockSettings as T;
  if (clean === "/api/ai/status") return {
    enabled: true,
    default_provider: "ollama",
    default_model: "qwen3-coder:30b",
    providers: [
      { name: "ollama", available: false, model: "qwen3-coder:30b", error: "Provider local no arrancado" },
      { name: "lmstudio", available: false, model: "local", error: "Provider local no arrancado" },
    ],
  } as T;
  if (clean === "/api/rag/documents") return [] as T;
  if (clean === "/api/security/status") return {
    app_env: "development",
    database_filename: "financial-os.sqlite",
    backups_available: mockBackups.length,
    encryption_ready: true,
    demo_data_policy: "Los datos demo deben estar identificados y excluidos de totales reales.",
  } as T;
  if (clean === "/api/security/backups") {
    if (init?.method === "POST") {
      const backup = {
        filename: `financial-${Date.now()}.sqlite`,
        size_bytes: 245760,
        created_at: new Date().toISOString(),
      };
      mockBackups.unshift(backup);
      return backup as T;
    }
    return mockBackups as T;
  }
  if (clean === "/api/security/integrity") return {
    status: "ok",
    database_ok: true,
    tables: ["accounts", "transactions", "documents", "household_bills"],
    issues: [],
  } as T;
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
  if (clean === "/api/investments/reconciliation") return mockReconciliation as T;
  if (clean === "/api/investments/prices/refresh")
    return { ok: true, updated: 0, failed: [], needs_manual_nav: [], updated_items: [], manual_required: [], skipped: [], errors: [] } as T;
  if (clean === "/api/recurring") {
    if (init?.method === "POST" && typeof init.body === "string") {
      const payload = JSON.parse(init.body) as import("./budgets").RecurringCreate;
      const now = new Date().toISOString();
      const item: import("./budgets").RecurringTransaction = {
        id: crypto.randomUUID(),
        name: payload.name,
        category_id: payload.category_id ?? null,
        account_id: payload.account_id ?? null,
        amount: payload.amount,
        currency: payload.currency ?? "EUR",
        type: payload.type,
        frequency: payload.frequency,
        day_of_month: payload.day_of_month ?? null,
        day_of_week: null,
        month_of_year: null,
        next_date: payload.next_date,
        active: true,
        description: payload.description ?? null,
        created_at: now,
        updated_at: now,
      };
      mockRecurring.unshift(item);
      return item as T;
    }
    return mockRecurring as T;
  }
  if (clean === "/api/recurring/candidates") return mockRecurringCandidates as T;
  if (clean === "/api/recurring/calendar") return mockCalendar as T;
  if (clean === "/api/household-bills") {
    if (init?.method === "POST" && typeof init.body === "string") {
      const payload = JSON.parse(init.body) as import("./household-bills").HouseholdBillCreate;
      const now = new Date().toISOString();
      const bill: import("./household-bills").HouseholdBill = {
        id: crypto.randomUUID(),
        provider: payload.provider,
        service_type: payload.service_type,
        period_start: payload.period_start,
        period_end: payload.period_end,
        amount: payload.amount,
        currency: payload.currency ?? "EUR",
        category_id: payload.category_id ?? null,
        is_recurring: payload.is_recurring ?? true,
        due_date: payload.due_date ?? null,
        paid_at: payload.paid_at ?? null,
        notes: payload.notes ?? null,
        created_at: now,
        updated_at: now,
      };
      mockHouseholdBills.unshift(bill);
      return bill as T;
    }
    return mockHouseholdBills as T;
  }
  if (clean === "/api/household-bills/summary") return mockHouseholdSummary as T;
  if (clean.startsWith("/api/household-bills/") && init?.method === "DELETE") return undefined as T;
  if (clean === "/api/market-intelligence/snapshot/macro") return mockMacroSnapshot as T;
  if (clean === "/api/market-intelligence/snapshot/market") return mockMarketSnapshot as T;
  if (clean === "/api/market-intelligence/snapshot/bonds") return mockBondSnapshot as T;
  if (clean === "/api/market-intelligence/snapshot/forex") return mockForexSnapshot as T;
  if (clean === "/api/market-intelligence/personal-impact") return mockPersonalImpact as T;
  if (clean === "/api/market-intelligence/ingest-status") return mockIngestStatus as T;
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
