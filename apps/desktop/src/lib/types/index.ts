export type AccountType =
  | "cash"
  | "bank"
  | "broker"
  | "savings"
  | "investment"
  | "mortgage"
  | "other";

export type TransactionType = "income" | "expense" | "transfer" | "investment";

export type CategoryType = "income" | "expense" | "transfer" | "investment";

export type TransactionSource = "manual" | "csv" | "pdf" | "system";

export type ImportStatus =
  | "pending"
  | "validated"
  | "imported"
  | "failed"
  | "rolled_back";

export interface Account {
  id: string;
  name: string;
  type: AccountType;
  institution: string | null;
  currency: string;
  current_balance: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Category {
  id: string;
  name: string;
  parent_id: string | null;
  type: CategoryType;
  icon: string | null;
  color: string | null;
  is_system: boolean;
  created_at: string;
  updated_at: string;
}

export interface Transaction {
  id: string;
  account_id: string;
  account_name: string | null;
  category_id: string | null;
  date: string;
  description: string;
  amount: string;
  currency: string;
  converted_amount: string | null;
  converted_currency: string | null;
  type: TransactionType;
  source: TransactionSource;
  source_name: string | null;
  external_id: string | null;
  import_batch_id: string | null;
  analytics_scope: "personal" | "excluded" | "pending";
  linked_transaction_id: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface HealthResponse {
  status: string;
  version: string;
}

export interface DashboardOverview {
  net_worth: string;
  liquidity: string;
  investments: string;
  monthly_income: string;
  monthly_expense: string;
  monthly_savings: string;
  savings_rate: number;
  currency: string;
}

export interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
  };
}

export interface ImportPreviewRow {
  row_number: number; date: string; account: string; category: string; amount: string;
  currency: string; description: string; status: "valid" | "invalid" | "duplicate" | "skipped";
  errors: string[]; warnings: string[];
}

export interface ImportPreview {
  import_batch_id: string; source_type: string; detected_source: string | null; columns: string[];
  rows_total: number; rows_valid: number; rows_invalid: number; rows_skipped: number;
  warnings_count: number; preview_rows: ImportPreviewRow[]; mapping: Record<string, string>;
}

export interface ImportBatch {
  id: string; source_name: string; source_type: string; file_name: string; status: ImportStatus;
  rows_total: number; rows_imported: number; rows_failed: number; created_at: string; completed_at: string | null;
}

export type AssetType = "stock" | "etf" | "fund" | "crypto" | "bond" | "cash" | "unknown" | "savings_account";
export type PriceSource = "yfinance" | "manual" | "mock" | "demo" | "seed";
export type OperationType =
  | "buy" | "sell" | "deposit" | "withdrawal"
  | "dividend" | "interest" | "fee";

export interface InvestmentAsset {
  id: string;
  name: string;
  ticker: string | null;
  isin: string | null;
  asset_type: AssetType;
  currency: string;
  region: string | null;
  sector: string | null;
  price_source: PriceSource;
  created_at: string;
  updated_at: string;
}

export interface Holding {
  id: string;
  account_id: string;
  asset_id: string;
  quantity: string;
  average_price: string;
  current_price: string | null;
  current_price_currency: string;
  current_price_updated_at: string | null;
  market_value: string | null;
  interest_rate: string | null;
  inception_date: string | null;
  created_at: string;
  updated_at: string;
  asset: InvestmentAsset;
}

export interface HoldingEnriched extends Holding {
  cost_basis: string;
  return_absolute: string | null;
  return_percent: number | null;
  accrued_interest: string | null;
  display_name: string;
  symbol: string | null;
  asset_type: AssetType;
  broker: string;
  invested_amount: string;
  unrealized_pnl: string;
  unrealized_pnl_pct: number;
  currency: string;
  is_mock: boolean;
  quality_score: number;
  warnings: string[];
}

export interface InvestmentOperation {
  id: string;
  account_id: string;
  asset_id: string;
  date: string;
  operation_type: OperationType;
  quantity: string | null;
  price: string | null;
  amount: string;
  currency: string;
  fees: string;
  source: string;
  created_at: string;
}

export interface AccountSummary {
  account_id: string;
  value: string;
  invested: string;
}

export interface InvestmentSummary {
  total_value: string;
  total_invested: string;
  return_absolute: string;
  return_percent: number;
  currency: string;
  by_account: AccountSummary[];
  last_updated: string | null;
}

export interface PriceRefreshResult {
  ok: boolean;
  updated: number;
  failed: string[];
  needs_manual_nav: string[];
  updated_items: {
    holding_id: string;
    name: string;
    symbol: string | null;
    old_price: string | null;
    new_price: string;
    currency: string;
    source: string;
  }[];
  manual_required: {
    holding_id: string;
    name: string;
    symbol: string | null;
    asset_type: AssetType;
    reason: string;
  }[];
  skipped: {
    holding_id: string;
    name: string;
    asset_type: AssetType;
    reason: string;
  }[];
  errors: string[];
}

// Market Watch
export type MarketCategory =
  | "indices_eu"
  | "indices_us"
  | "indices_asia"
  | "crypto"
  | "fx"
  | "bonds"
  | "commodities"
  | "volatility";

export type FreshnessStatus =
  | "live"      // dato ≤5 min, mercado abierto
  | "fresh"     // dato ≤15 min
  | "delayed"   // dato retrasado 15–60 min
  | "eod"       // último cierre de mercado
  | "closed"    // mercado confirmado cerrado
  | "stale"     // caché vencida (todos los providers fallaron)
  | "error"     // sin datos disponibles
  | "unknown";  // sin información de frescura

export interface MarketQuote {
  symbol: string;
  name: string;
  category: MarketCategory;
  price: number | null;
  change_pct: number | null;
  change_absolute: number | null;
  currency: string;
  sparkline: number[];
  last_updated: string;
  market_open: boolean;
  // Campos de Fase 4.5 — multi-provider
  freshness_status: FreshnessStatus;
  source: string;
  is_fallback: boolean;
  is_stale: boolean;
  warning: string | null;
  confidence_score: number;
}

// ── Fase 5 — Economic Intelligence ───────────────────────────────────────────

export type EconomicRegion = "ES" | "EA" | "US" | "GLOBAL";
export type EconomicIndicatorType =
  | "inflation" | "core_inflation" | "unemployment" | "gdp"
  | "policy_rate" | "bond_10y" | "euribor" | "index" | "forex";
export type ImpactInterpretation = "favorable" | "neutral" | "adverse" | "no_data";

export interface EconomicIndicator {
  series_id: string;
  region: EconomicRegion;
  indicator: EconomicIndicatorType;
  name: string;
  value: number | null;
  prev_value: number | null;
  change: number | null;
  period: string;
  unit: string;
  source: string;
  observation_date: string;
  is_stale: boolean;
}

export interface RegionSnapshot {
  region: EconomicRegion;
  indicators: EconomicIndicator[];
}

export interface MacroSnapshot {
  spain: RegionSnapshot;
  eurozone: RegionSnapshot;
  us: RegionSnapshot;
  last_refreshed: string;
}

export interface ImpactItem {
  title: string;
  macro_value: number | null;
  personal_value: number | null;
  delta: number | null;
  interpretation: ImpactInterpretation;
  description: string;
}

export interface PersonalImpact {
  inflation_vs_savings: ImpactItem;
  rates_vs_liquidity: ImpactItem;
  market_vs_portfolio: ImpactItem;
  purchasing_power: ImpactItem;
}
