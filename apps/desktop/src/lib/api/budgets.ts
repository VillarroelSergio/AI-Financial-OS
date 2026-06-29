import { api } from "./client";

// ── Budget types ──────────────────────────────────────────────────────────────

export interface Budget {
  id: string;
  category_id: string;
  period: "monthly" | "yearly";
  amount: number;
  alert_threshold_pct: number;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface BudgetCreate {
  category_id: string;
  period?: "monthly" | "yearly";
  amount: number;
  alert_threshold_pct?: number;
}

export interface BudgetUpdate {
  amount?: number;
  alert_threshold_pct?: number;
  active?: boolean;
}

export interface BudgetComparisonItem {
  budget_id: string;
  category_id: string;
  category_name: string;
  budget_amount: number;
  actual_amount: number;
  remaining: number;
  consumption_pct: number;
  alert: boolean;
  over_budget: boolean;
  period: string;
}

// ── Recurring types ───────────────────────────────────────────────────────────

export interface RecurringTransaction {
  id: string;
  name: string;
  category_id: string | null;
  account_id: string | null;
  amount: number;
  currency: string;
  type: "income" | "expense";
  frequency: "monthly" | "weekly" | "yearly";
  day_of_month: number | null;
  day_of_week: number | null;
  month_of_year: number | null;
  next_date: string;
  active: boolean;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface RecurringCreate {
  name: string;
  category_id?: string | null;
  account_id?: string | null;
  amount: number;
  currency?: string;
  type: "income" | "expense";
  frequency: "monthly" | "weekly" | "yearly";
  day_of_month?: number | null;
  next_date: string;
  description?: string | null;
}

export interface CalendarEvent {
  recurring_id: string;
  name: string;
  amount: number;
  type: "income" | "expense";
  date: string;
  category_name: string | null;
}

// ── Cashflow types ────────────────────────────────────────────────────────────

export interface MonthForecast {
  month: string;
  projected_income: number;
  projected_expenses: number;
  projected_balance: number;
  historical_avg_income: number;
  historical_avg_expenses: number;
  recurring_income: number;
  recurring_expenses: number;
}

export interface CashflowForecast {
  generated_at: string;
  months: MonthForecast[];
}

// ── API functions ─────────────────────────────────────────────────────────────

export const fetchBudgets = (): Promise<Budget[]> => api.get<Budget[]>("/api/budgets");
export const createBudget = (body: BudgetCreate): Promise<Budget> => api.post<Budget>("/api/budgets", body);
export const updateBudget = (id: string, body: BudgetUpdate): Promise<Budget> => api.patch<Budget>(`/api/budgets/${id}`, body);
export const deleteBudget = (id: string): Promise<void> => api.delete<void>(`/api/budgets/${id}`);
export const fetchBudgetComparison = (month?: string): Promise<BudgetComparisonItem[]> =>
  api.get<BudgetComparisonItem[]>(`/api/budgets/comparison${month ? `?month=${month}` : ""}`);

export const fetchRecurring = (): Promise<RecurringTransaction[]> => api.get<RecurringTransaction[]>("/api/recurring");
export const createRecurring = (body: RecurringCreate): Promise<RecurringTransaction> => api.post<RecurringTransaction>("/api/recurring", body);
export const updateRecurring = (id: string, body: Partial<RecurringCreate>): Promise<RecurringTransaction> => api.patch<RecurringTransaction>(`/api/recurring/${id}`, body);
export const deleteRecurring = (id: string): Promise<void> => api.delete<void>(`/api/recurring/${id}`);
export const fetchCalendar = (days?: number): Promise<CalendarEvent[]> =>
  api.get<CalendarEvent[]>(`/api/recurring/calendar${days ? `?days=${days}` : ""}`);

export const fetchCashflowForecast = (months?: number): Promise<CashflowForecast> =>
  api.get<CashflowForecast>(`/api/cashflow/forecast${months ? `?months=${months}` : ""}`);
