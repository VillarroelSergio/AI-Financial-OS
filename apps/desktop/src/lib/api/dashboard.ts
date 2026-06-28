import type { DashboardOverview } from "@/lib/types";
import { api } from "./client";

export interface CategorySpending {
  category_id: string | null;
  category: string;
  amount: string;
  percentage: number;
}

export interface SpendingData {
  month: string;
  period_type: "month" | "year";
  total_expense: string;
  total_income: string;
  net_savings: string;
  savings_rate: number;
  transaction_count: number;
  average_daily_expense: string;
  by_category: CategorySpending[];
}

export interface CategoryTransaction {
  id: string;
  date: string;
  description: string;
  account_name: string;
  amount: string;
  currency: string;
  category: string;
  type: "expense" | "income" | "transfer" | "investment";
  notes: string | null;
}

export interface CategorySpendingDetail {
  category_id: string | null;
  category: string;
  period: string;
  period_type: "month" | "year";
  total: string;
  percentage: number;
  transaction_count: number;
  average_transaction: string;
  transactions: CategoryTransaction[];
}

export const fetchOverview = () => api.get<DashboardOverview>("/api/dashboard/overview");
export const fetchSpending = (period: { month?: string; year?: number }) => {
  const query = period.year ? `year=${period.year}` : `month=${period.month}`;
  return api.get<SpendingData>(`/api/dashboard/spending?${query}`);
};
export const fetchSpendingYears = () => api.get<{ years: number[] }>("/api/dashboard/spending/years");
export const fetchCategorySpendingDetail = (
  categoryId: string | null,
  period: { month?: string; year?: number },
) => {
  const params = new URLSearchParams();
  if (categoryId) params.set("category_id", categoryId);
  if (period.year) params.set("year", String(period.year));
  else if (period.month) params.set("month", period.month);
  return api.get<CategorySpendingDetail>(`/api/dashboard/spending/category-detail?${params.toString()}`);
};
