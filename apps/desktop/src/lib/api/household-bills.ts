import { api } from "./client";

export interface HouseholdBill {
  id: string;
  provider: string;
  service_type: string;
  period_start: string;
  period_end: string;
  amount: string;
  currency: string;
  category_id: string | null;
  is_recurring: boolean;
  due_date: string | null;
  paid_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface HouseholdBillCreate {
  provider: string;
  service_type: string;
  period_start: string;
  period_end: string;
  amount: string;
  currency?: string;
  category_id?: string | null;
  is_recurring?: boolean;
  due_date?: string | null;
  paid_at?: string | null;
  notes?: string | null;
}

export interface HouseholdBillSummaryItem {
  service_type: string;
  provider: string;
  bills_count: number;
  last_amount: number;
  previous_amount: number | null;
  change_pct: number | null;
  average_amount: number;
  next_estimate: number;
  anomaly: boolean;
  latest_period: string;
}

export interface HouseholdBillSummary {
  generated_at: string;
  total_monthly_estimate: number;
  items: HouseholdBillSummaryItem[];
}

export const fetchHouseholdBills = () => api.get<HouseholdBill[]>("/api/household-bills");
export const fetchHouseholdBillSummary = () => api.get<HouseholdBillSummary>("/api/household-bills/summary");
export const createHouseholdBill = (body: HouseholdBillCreate) => api.post<HouseholdBill>("/api/household-bills", body);
export const deleteHouseholdBill = (id: string) => api.delete<void>(`/api/household-bills/${id}`);
