import type { DashboardOverview } from "@/lib/types";
import { api } from "./client";
import { buildQueryString } from "./queryParams";

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
export const fetchSpending = (period: { month?: string; year?: number }) =>
  api.get<SpendingData>(`/api/dashboard/spending${buildQueryString({ year: period.year, month: period.year ? undefined : period.month })}`);
export const fetchSpendingYears = () => api.get<{ years: number[] }>("/api/dashboard/spending/years");

export interface MonthlySpendingPoint {
  month: string;
  income: string;
  expense: string;
  savings: string;
}

export const fetchSpendingMonthly = (months = 12, year?: number) =>
  api.get<MonthlySpendingPoint[]>(
    `/api/dashboard/spending/monthly${buildQueryString({ months, year })}`,
  );
export const fetchCategorySpendingDetail = (
  categoryId: string | null,
  period: { month?: string; year?: number },
) =>
  api.get<CategorySpendingDetail>(`/api/dashboard/spending/category-detail${buildQueryString({
    category_id: categoryId,
    year: period.year,
    month: period.year ? undefined : period.month,
  })}`);
