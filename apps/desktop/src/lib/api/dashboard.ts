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
  total_expense: string;
  total_income: string;
  by_category: CategorySpending[];
}

export const fetchOverview = () => api.get<DashboardOverview>("/api/dashboard/overview");
export const fetchSpending = (month: string) =>
  api.get<SpendingData>(`/api/dashboard/spending?month=${month}`);
