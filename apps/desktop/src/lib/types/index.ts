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
  currency: string; description: string; status: "valid" | "invalid" | "duplicate";
  errors: string[]; warnings: string[];
}

export interface ImportPreview {
  import_batch_id: string; source_type: "monefy" | "generic_csv"; columns: string[];
  rows_total: number; rows_valid: number; rows_invalid: number; warnings_count: number;
  preview_rows: ImportPreviewRow[]; mapping: Record<string, string>;
}

export interface ImportBatch {
  id: string; source_name: string; source_type: string; file_name: string; status: ImportStatus;
  rows_total: number; rows_imported: number; rows_failed: number; created_at: string; completed_at: string | null;
}

export type AssetType = "stock" | "etf" | "fund" | "savings_account";
export type PriceSource = "yfinance" | "manual";
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
  updated: number;
  failed: string[];
  needs_manual_nav: string[];
}
