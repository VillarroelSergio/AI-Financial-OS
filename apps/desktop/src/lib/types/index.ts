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
