import type { Account, Category, Transaction, DashboardOverview, HoldingEnriched, InvestmentAsset, InvestmentSummary } from "@/lib/types";
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
  total_expense: "1095.89",
  total_income: "2800.00",
  by_category: mockSpendingCategories,
};

const mockInvestmentAssets: InvestmentAsset[] = [
  {
    id: "asset-aapl", name: "Apple Inc.", ticker: "AAPL", isin: "US0378331005",
    asset_type: "stock", currency: "USD", region: "US", sector: "Technology",
    price_source: "yfinance", created_at: "2024-01-01T00:00:00", updated_at: "2026-06-23T10:00:00",
  },
  {
    id: "asset-tef", name: "Telefónica", ticker: "TEF.MC", isin: "ES0178430E18",
    asset_type: "stock", currency: "EUR", region: "ES", sector: "Telecom",
    price_source: "yfinance", created_at: "2024-01-01T00:00:00", updated_at: "2026-06-23T10:00:00",
  },
  {
    id: "asset-vg500", name: "Vanguard US 500 Index Inst Plus", ticker: null, isin: "IE00B5B3X895",
    asset_type: "fund", currency: "EUR", region: "US", sector: null,
    price_source: "manual", created_at: "2024-01-01T00:00:00", updated_at: "2026-06-23T10:00:00",
  },
  {
    id: "asset-ishares", name: "iShares North America Index Inst", ticker: null, isin: "IE00B14X4S71",
    asset_type: "fund", currency: "EUR", region: "US", sector: null,
    price_source: "manual", created_at: "2024-01-01T00:00:00", updated_at: "2026-06-23T10:00:00",
  },
  {
    id: "asset-cleome", name: "Cleome Index USA Equities", ticker: null, isin: "LU1045609586",
    asset_type: "fund", currency: "EUR", region: "US", sector: null,
    price_source: "manual", created_at: "2024-01-01T00:00:00", updated_at: "2026-06-23T10:00:00",
  },
  {
    id: "asset-tr-savings", name: "Cuenta Remunerada Trade Republic", ticker: null, isin: null,
    asset_type: "savings_account", currency: "EUR", region: null, sector: null,
    price_source: "manual", created_at: "2024-01-01T00:00:00", updated_at: "2026-06-23T10:00:00",
  },
];

const assetMap = Object.fromEntries(mockInvestmentAssets.map(a => [a.id, a]));

const mockHoldings: HoldingEnriched[] = [
  {
    id: "h-aapl", account_id: "mock-acc-tr", asset_id: "asset-aapl",
    quantity: "15", average_price: "150.0000", current_price: "192.5000",
    current_price_currency: "USD", current_price_updated_at: "2026-06-23T10:00:00",
    market_value: "2673.61", interest_rate: null, inception_date: null,
    created_at: "2024-01-01T00:00:00", updated_at: "2026-06-23T10:00:00",
    asset: assetMap["asset-aapl"],
    cost_basis: "2250.0000", return_absolute: "423.61", return_percent: 18.83, accrued_interest: null,
  },
  {
    id: "h-tef", account_id: "mock-acc-tr", asset_id: "asset-tef",
    quantity: "200", average_price: "3.9500", current_price: "4.2100",
    current_price_currency: "EUR", current_price_updated_at: "2026-06-23T10:00:00",
    market_value: "842.00", interest_rate: null, inception_date: null,
    created_at: "2024-01-01T00:00:00", updated_at: "2026-06-23T10:00:00",
    asset: assetMap["asset-tef"],
    cost_basis: "790.0000", return_absolute: "52.00", return_percent: 6.58, accrued_interest: null,
  },
  {
    id: "h-vg500", account_id: "mock-acc-finizens", asset_id: "asset-vg500",
    quantity: "4.59", average_price: "420.0000", current_price: "576.1900",
    current_price_currency: "EUR", current_price_updated_at: "2026-06-23T10:00:00",
    market_value: "2644.71", interest_rate: null, inception_date: null,
    created_at: "2024-01-01T00:00:00", updated_at: "2026-06-23T10:00:00",
    asset: assetMap["asset-vg500"],
    cost_basis: "1927.8000", return_absolute: "716.91", return_percent: 37.19, accrued_interest: null,
  },
  {
    id: "h-ishares", account_id: "mock-acc-finizens", asset_id: "asset-ishares",
    quantity: "42.62", average_price: "28.0000", current_price: "39.1100",
    current_price_currency: "EUR", current_price_updated_at: "2026-06-23T10:00:00",
    market_value: "1667.04", interest_rate: null, inception_date: null,
    created_at: "2024-01-01T00:00:00", updated_at: "2026-06-23T10:00:00",
    asset: assetMap["asset-ishares"],
    cost_basis: "1193.3600", return_absolute: "473.68", return_percent: 39.69, accrued_interest: null,
  },
  {
    id: "h-cleome", account_id: "mock-acc-finizens", asset_id: "asset-cleome",
    quantity: "0.44", average_price: "1800.0000", current_price: "2858.9500",
    current_price_currency: "EUR", current_price_updated_at: "2026-06-23T10:00:00",
    market_value: "1257.94", interest_rate: null, inception_date: null,
    created_at: "2024-01-01T00:00:00", updated_at: "2026-06-23T10:00:00",
    asset: assetMap["asset-cleome"],
    cost_basis: "792.0000", return_absolute: "465.94", return_percent: 58.83, accrued_interest: null,
  },
  {
    id: "h-savings", account_id: "mock-acc-tr-savings", asset_id: "asset-tr-savings",
    quantity: "5000.00000000", average_price: "1.0000", current_price: null,
    current_price_currency: "EUR", current_price_updated_at: null,
    market_value: "5000.00", interest_rate: "0.0400", inception_date: "2025-01-01",
    created_at: "2025-01-01T00:00:00", updated_at: "2026-06-23T10:00:00",
    asset: assetMap["asset-tr-savings"],
    cost_basis: "5000.00000000", return_absolute: null, return_percent: null, accrued_interest: "72.33",
  },
];

const mockInvestmentSummary: InvestmentSummary = {
  total_value: "14085.30",
  total_invested: "11953.16",
  return_absolute: "2132.14",
  return_percent: 17.84,
  currency: "EUR",
  by_account: [
    { account_id: "mock-acc-tr", value: "3515.61", invested: "3040.00" },
    { account_id: "mock-acc-finizens", value: "5569.69", invested: "3913.16" },
    { account_id: "mock-acc-tr-savings", value: "5000.00", invested: "5000.00" },
  ],
  last_updated: "2026-06-23T10:00:00",
};

const mockSettings: AppSetting[] = [
  { id: "set-1", key: "app.language", value_json: '"es"', created_at: "2024-01-01T00:00:00", updated_at: "2024-01-01T00:00:00" },
  { id: "set-2", key: "theme.mode", value_json: '"dark"', created_at: "2024-01-01T00:00:00", updated_at: "2024-01-01T00:00:00" },
  { id: "set-3", key: "app.currency", value_json: '"EUR"', created_at: "2024-01-01T00:00:00", updated_at: "2024-01-01T00:00:00" },
];

export function getMockResponse<T>(path: string): T {
  const clean = path.split("?")[0];

  if (clean === "/api/accounts") return mockAccounts as T;
  if (clean === "/api/categories") return mockCategories as T;
  if (clean === "/api/transactions") return mockTransactions as T;
  if (clean === "/api/dashboard/overview") return mockOverview as T;
  if (clean === "/api/dashboard/spending") return mockSpending as T;
  if (clean === "/api/settings") return mockSettings as T;
  if (clean === "/api/investments/assets") return mockInvestmentAssets as T;
  if (clean === "/api/investments/holdings") return mockHoldings as T;
  if (clean === "/api/investments/summary") return mockInvestmentSummary as T;
  if (clean === "/api/investments/prices/refresh")
    return { updated: 2, failed: [], needs_manual_nav: ["asset-vg500", "asset-ishares", "asset-cleome"] } as T;

  throw new Error(`[mock] No mock defined for: ${path}`);
}
